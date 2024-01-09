from opaque_registry.api.errors.base import ApiException


class PackageAlreadyExistsError(ApiException):
    def __init__(self, package_id: str):
        super().__init__(
            status_code=409,
            message=f"Package with id '{package_id}' already exists",
            details={"package_id": package_id},
        )


class PackageNotFoundError(ApiException):
    def __init__(self, package_id: str):
        super().__init__(
            status_code=404,
            message=f"Package with id '{package_id}' not found",
            details={"package_id": package_id},
        )


class PackageVersionAlreadyExistsError(ApiException):
    def __init__(self, package_id: str, package_version: str):
        super().__init__(
            status_code=409,
            message=f"Package version '{package_version}' already exists for package '{package_id}'",
            details={"package_id": package_id, "package_version": package_version},
        )


class PackageVersionNotYetPublished(ApiException):
    def __init__(self, package_id: str, package_version: str):
        super().__init__(
            status_code=409,
            message=f"Package version '{package_version}' for package '{package_id}' has not yet been published",
            details={"package_id": package_id, "package_version": package_version},
        )


class SelfReferencingPackageError(ApiException):
    def __init__(self, package_id: str, package_version: str, dependency: str):
        super().__init__(
            status_code=409,
            message=f"Package '{package_id}' with version '{package_version}' cannot depend on itself",
            details={
                "package_id": package_id,
                "package_version": package_version,
                "dependency": dependency,
            },
        )
