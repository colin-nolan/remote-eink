from image_display_service.api.display import display_id_handler, DisplayController, HTTPStatus


@display_id_handler
def search(display_controller: DisplayController):
    return display_controller.sleeping, HTTPStatus.OK


@display_id_handler
def put(display_controller: DisplayController, body: bytes):
    if body and not display_controller.sleeping:
        display_controller.sleep()
    elif not body and display_controller.sleeping:
        display_controller.wake()
    assert display_controller.sleeping == body
    return True, HTTPStatus.OK
