from remote_eink.api.display import display_id_handler, DisplayController, HTTPStatus, to_target_process


@to_target_process
@display_id_handler
def search(display_controller: DisplayController):
    return display_controller.driver.sleeping, HTTPStatus.OK


@to_target_process
@display_id_handler
def put(display_controller: DisplayController, body: bytes):
    if body and not display_controller.driver.sleeping:
        display_controller.driver.sleep()
    elif not body and display_controller.driver.sleeping:
        display_controller.driver.wake()
    assert display_controller.driver.sleeping == body
    return True, HTTPStatus.OK
