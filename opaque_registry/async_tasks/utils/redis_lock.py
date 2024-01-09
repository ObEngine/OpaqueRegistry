import time
import uuid

import redis


class LockException(Exception):
    """
    Generic exception for Locks.
    """

    pass


class LockTimeoutException(Exception):
    """
    Raised whenever timeout occurs while trying to acquire lock.
    """

    pass


class BaseLock(object):
    """
    Interface for implementing custom Lock implementations. This class must be
    sub-classed in order to implement a custom Lock with custom logic or
    different backend or both.

    Basic Usage (an example of our imaginary datastore)

    >>> class MyLock(BaseLock):
    ...     def __init__(self, lock_name, **kwargs):
    ...         super(MyLock, self).__init__(lock_name, **kwargs)
    ...         if self.client is None:
    ...             self.client = mybackend.Client(host='localhost', port=1234)
    ...         self._owner = None
    ...
    ...     def _acquire(self):
    ...         if self.client.get(self.lock_name) is not None:
    ...             owner = str(uuid.uuid4()) # or anythin you want
    ...             self.client.set(self.lock_name, owner)
    ...             self._owner = owner
    ...             if self.expire is not None:
    ...                 self.client.expire(self.lock_name, self.expire)
    ...             return True
    ...         return False
    ...
    ...     def _release(self):
    ...         if self._owner is not None:
    ...             lock_val = self.client.get(self.lock_name)
    ...             if lock_val == self._owner:
    ...                 self.client.delete(self.lock_name)
    ...
    ...     def _locked(self):
    ...         if self.client.get(self.lock_name) is not None:
    ...             return True
    ...         return False
    """

    def __init__(self, lock_name, expire: float | None = None):
        """
        :param str lock_name: name of the lock to uniquely identify the lock
                              between processes.
        :param str namespace: Optional namespace to namespace lock keys for
                              your application in order to avoid conflicts.
        :param float expire: set lock expiry time. If explicitly set to `None`,
                             lock will not expire.
        :param float timeout: set timeout to acquire lock
        :param float retry_interval: set interval for trying acquiring lock
                                     after the timeout interval has elapsed.
        :param client: supported client object for the backend of your choice.
        """
        self.lock_name = lock_name
        self.expire = expire
        self._keep_alive = False

    @property
    def _locked(self):
        """
        Implementation of method to check if lock has been acquired. Must be
        implemented in the sub-class.

        :returns: if the lock is acquired or not
        :rtype: bool
        """

        raise NotImplementedError("Must be implemented in the sub-class.")

    def locked(self):
        """
        Return if the lock has been acquired or not.

        :returns: True indicating that a lock has been acquired ot a
                  shared resource is locked.
        :rtype: bool
        """

        return self._locked

    def _acquire(self):
        """
        Implementation of acquiring a lock in a non-blocking fashion. Must be
        implemented in the sub-class. :meth:`acquire` makes use of this
        implementation to provide blocking and non-blocking implementations.

        :returns: if the lock was successfully acquired or not
        :rtype: bool
        """

        raise NotImplementedError("Must be implemented in the sub-class.")

    def acquire(
        self, blocking=True, timeout: float | None = None, retry_interval: float = 0.1
    ):
        """
        Acquire a lock, blocking or non-blocking.

        :param bool blocking: acquire a lock in a blocking or non-blocking
                              fashion. Defaults to True.
        :returns: if the lock was successfully acquired or not
        :rtype: bool
        """

        if blocking is True:
            if timeout is None:
                while self._acquire() is not True:
                    time.sleep(retry_interval)
            else:
                while timeout >= 0:
                    if self._acquire() is not True:
                        timeout -= retry_interval
                        if timeout > 0:
                            time.sleep(retry_interval)
                    else:
                        return True
            raise LockTimeoutException(
                "Timeout elapsed after %s seconds "
                "while trying to acquiring "
                "lock." % self.timeout
            )
        else:
            return self._acquire()

    def _release(self):
        """
        Implementation of releasing an acquired lock. Must be implemented in
        the sub-class.
        """

        raise NotImplementedError("Must be implemented in the sub-class.")

    def release(self):
        """
        Release a lock.
        """

        return self._release()

    def _renew(self) -> bool:
        """
        Implementation of renewing an acquired lock. Must be implemented in
        the sub-class.
        """
        raise NotImplementedError("Must be implemented in the sub-class")

    def renew(self) -> bool:
        """
        Renew a lock that is already acquired.
        """
        return self._renew()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()

    def __del__(self):
        try:
            self.release()
        except LockException:
            pass

    def keep_alive_until_expiration(self):
        self._keep_alive = True


class RedisLock(BaseLock):
    """
    Implementation of lock with Redis as the backend for synchronization.

    Basic Usage:

    >>> import redis
    >>> import sherlock
    >>> from sherlock import RedisLock
    >>>
    >>> # Global configuration of defaults
    >>> sherlock.configure(expire=120, timeout=20)
    >>>
    >>> # Create a lock instance
    >>> lock = RedisLock('my_lock')
    >>>
    >>> # Acquire a lock in Redis, global backend and client configuration need
    >>> # not be configured since we are using a backend specific lock.
    >>> lock.acquire()
    True
    >>>
    >>> # Check if the lock has been acquired
    >>> lock.locked()
    True
    >>>
    >>> # Release the acquired lock
    >>> lock.release()
    >>>
    >>> # Check if the lock has been acquired
    >>> lock.locked()
    False
    >>>
    >>> # Use this client object
    >>> client = redis.StrictRedis()
    >>>
    >>> # Create a lock instance with custom client object
    >>> lock = RedisLock('my_lock', client=client)
    >>>
    >>> # To override the defaults, just past the configurations as parameters
    >>> lock = RedisLock('my_lock', client=client, expire=1, timeout=5)
    >>>
    >>> # Acquire a lock using the with_statement
    >>> with RedisLock('my_lock') as lock:
    ...     # do some stuff with your acquired resource
    ...     pass
    """

    _acquire_script = """
    local result = redis.call('SETNX', KEYS[1], ARGV[1])
    local expire = tonumber(ARGV[2])
    if result == 1 and expire ~= -1 then
        redis.call('EXPIRE', KEYS[1], expire)
    end
    return result
    """

    _release_script = """
    local result = 0
    if redis.call('GET', KEYS[1]) == ARGV[1] then
        redis.call('DEL', KEYS[1])
        result = 1
    end
    return result
    """

    _renew_script = """
    local result = 0
    if redis.call('GET', KEYS[1]) == ARGV[1] then
        if ARGV[2] ~= -1 then
            redis.call('EXPIRE', KEYS[1], ARGV[2])
        else
            redis.call('PERSIST', KEYS[1])
        end
        result = 1
    end
    return result
    """

    _modify_expire_script = """
    local result = 0
    if redis.call('GET', KEYS[1]) == ARGV[1] then
        if ARGV[2] ~= -1 then
            redis.call('EXPIRE', KEYS[1], ARGV[2])
        else
            redis.call('PERSIST', KEYS[1])
        end
        result = 1
    end
    return result
    """

    def __init__(
        self, client: redis.StrictRedis, lock_name: str, expire: float | None = None
    ):
        """
        :param str lock_name: name of the lock to uniquely identify the lock
                              between processes.
        :param str namespace: Optional namespace to namespace lock keys for
                              your application in order to avoid conflicts.
        :param float expire: set lock expiry time. If explicitly set to `None`,
                             lock will not expire.
        :param float timeout: set timeout to acquire lock
        :param float retry_interval: set interval for trying acquiring lock
                                     after the timeout interval has elapsed.
        :param client: supported client object for the backend of your choice.
        """
        super(RedisLock, self).__init__(
            lock_name=lock_name,
            expire=expire,
        )

        self.client = client

        self._owner = None

        # Register Lua script
        self._acquire_func = self.client.register_script(self._acquire_script)
        self._release_func = self.client.register_script(self._release_script)
        self._renew_func = self.client.register_script(self._renew_script)

    def _acquire(self):
        owner = str(uuid.uuid4())
        if self.expire is None:
            expire = -1
        else:
            expire = self.expire
        if self._acquire_func(keys=[self.lock_name], args=[owner, expire]) != 1:
            return False
        self._owner = owner
        return True

    def _release(self):
        if self._owner is None:
            raise LockException("Lock was not set by this process.")

        if self._release_func(keys=[self.lock_name], args=[self._owner]) != 1:
            raise LockException(
                "Lock could not be released because it was "
                "not acquired by this instance."
            )

        self._owner = None

    def _renew(self) -> bool:
        if self._owner is None:
            raise LockException("Lock was not set by this process.")

        if (
            self._renew_func(keys=[self.lock_name], args=[self._owner, self.expire])
            != 1
        ):
            return False
        return True

    @property
    def _locked(self):
        if self.client.get(self.lock_name) is None:
            return False
        return True
