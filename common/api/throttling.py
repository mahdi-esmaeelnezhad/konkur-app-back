from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class BurstAnonThrottle(AnonRateThrottle):
    scope = "burst_anon"


class BurstUserThrottle(UserRateThrottle):
    scope = "burst_user"


class AuthThrottle(AnonRateThrottle):
    scope = "auth"


class SensitiveUserThrottle(UserRateThrottle):
    scope = "sensitive"
