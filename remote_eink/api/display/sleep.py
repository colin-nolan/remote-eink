from remote_eink.api.display._common import (
    HTTPStatus,
    RemoteThreadDisplayDriver,
    handle_display_controller_not_found_response,
)


@handle_display_controller_not_found_response
def search(displayId: str) -> tuple[bool, int]:
    display_driver = RemoteThreadDisplayDriver(displayId)
    return display_driver.sleeping, HTTPStatus.OK


@handle_display_controller_not_found_response
def put(displayId: str, body: bytes) -> tuple[bool, int]:
    display_driver = RemoteThreadDisplayDriver(displayId)
    if body and not display_driver.sleeping:
        display_driver.sleep()
    elif not body and display_driver.sleeping:
        display_driver.wake()
    assert display_driver.sleeping == body
    return True, HTTPStatus.OK
