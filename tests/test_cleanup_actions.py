from pathlib import Path

from app.modules.cleanup.actions import get_thumbnail_cache_paths, is_safe_cleanup_path


def test_cleanup_path_must_be_inside_allowed_root(tmp_path):
    allowed = tmp_path / "cache"
    target = allowed / "child"
    target.mkdir(parents=True)

    assert is_safe_cleanup_path(target, [allowed]) is True


def test_cleanup_path_rejects_personal_folders(tmp_path):
    downloads = tmp_path / "Downloads"
    downloads.mkdir()

    assert is_safe_cleanup_path(downloads, [tmp_path]) is False


def test_cleanup_path_rejects_sibling_path(tmp_path):
    allowed = tmp_path / "cache"
    sibling = tmp_path / "other"
    allowed.mkdir()
    sibling.mkdir()

    assert is_safe_cleanup_path(sibling, [allowed]) is False


def test_thumbnail_cache_paths_only_include_cache_files(tmp_path):
    explorer = tmp_path / "Microsoft" / "Windows" / "Explorer"
    explorer.mkdir(parents=True)
    thumb = explorer / "thumbcache_256.db"
    icon = explorer / "iconcache_32.db"
    unrelated = explorer / "settings.dat"
    thumb.write_text("x", encoding="utf-8")
    icon.write_text("x", encoding="utf-8")
    unrelated.write_text("x", encoding="utf-8")

    paths = get_thumbnail_cache_paths(tmp_path)

    assert set(paths) == {thumb, icon}
