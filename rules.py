from models import JobPost

REMOTE_CLOSED = "Remote role not open to Bangladesh"
NO_SUPPORT = "Role outside Bangladesh without visa or relocation support"


def check_deal_breakers(job: JobPost) -> list[str]:
    if job.work_mode == "remote":
        # Not stated (None) counts as closed
        return [] if job.open_to_bd is True else [REMOTE_CLOSED]

    # onsite, hybrid or work_mode not stated: need visa or relocation support
    if job.visa_support is True or job.relocation_support is True:
        return []
    return [NO_SUPPORT]
