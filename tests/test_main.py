from app.main import main


def test_main_initializes_application(caplog):
    with caplog.at_level("INFO"):
        main()

    assert "Starting MaukaKhoj" in caplog.text
    assert "MaukaKhoj initialized successfully" in caplog.text
