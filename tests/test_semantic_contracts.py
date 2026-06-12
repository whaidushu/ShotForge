from shotforge.core.semantic_contracts import build_semantic_contract


def test_compound_subject_is_atomic_entity():
    contract = build_semantic_contract("一只赛博猫在雨夜上海屋顶追逐发光无人机", "zh")

    assert "cyber cat" in contract["required_elements"]
    assert "cat" not in contract["required_elements"]
    assert any("ordinary" in item for item in contract["negative_constraints"])
    assert any("indivisible" in item for item in contract["identity_constraints"])


def test_robot_dog_and_bread_person_generalize_identity_contracts():
    robot_dog = build_semantic_contract("机器狗冲向红色大门", "zh")
    bread_person = build_semantic_contract("面包人压住机器人", "zh")

    assert "robot dog" in robot_dog["required_elements"]
    assert any("mechanical" in item for item in robot_dog["identity_constraints"])
    assert "bread person" in bread_person["required_elements"]
    assert any("bread material" in item for item in bread_person["identity_constraints"])


def test_action_contracts_capture_direction_and_contact():
    rush = build_semantic_contract("机器狗冲向无人机", "zh")
    attack = build_semantic_contract("面包人杀向机器人", "zh")
    pin = build_semantic_contract("机器人压住面包人", "zh")

    assert any(action["label"] == "rush_toward" for action in rush["actions"])
    assert any("destination in front" in item for item in rush["spatial_relationships"])
    assert any(action["label"] == "attack_toward" for action in attack["actions"])
    assert any("attack intent" in item for item in attack["motion_contracts"])
    assert any(action["label"] == "pin_down" for action in pin["actions"])
    assert any("on top of" in item for item in pin["spatial_relationships"])


def test_chase_contract_requires_target_ahead_of_actor():
    contract = build_semantic_contract("A robot dog chases a glowing drone across a rooftop", "en")

    assert "robot dog" in contract["required_elements"]
    assert "glowing drone" in contract["required_elements"]
    assert any("glowing drone is ahead of robot dog" in item for item in contract["spatial_relationships"])
    assert any("glowing drone behind robot dog" in item for item in contract["negative_constraints"])
