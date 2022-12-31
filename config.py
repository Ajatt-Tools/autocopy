from types import SimpleNamespace

from aqt import mw


def get_config() -> dict:
    return mw.addonManager.getConfig(__name__)


def write_config():
    return mw.addonManager.writeConfig(__name__, config.__dict__)


config = SimpleNamespace(**get_config())
