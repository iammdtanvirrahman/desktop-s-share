from nexus_agent.input_control import InputController

def test_remote_input_is_disabled_by_default():
    controller = InputController(1920, 1080, allowed=False)
    controller.set_active(True)
    assert controller.active is False
    controller.handle('{"type":"click","button":"left"}')

def test_remote_input_can_be_deactivated():
    controller = InputController(1920, 1080, allowed=False)
    controller.set_active(False)
    assert controller.active is False
