"""STORY-007: installing the git pre-commit adapter."""

import subprocess

from amigos import hooks
from amigos.cli import main


def test_install_writes_an_executable_hook(git_repo, capsys):
    assert main(["hooks", "install", "--root", str(git_repo)]) == 0
    path = hooks.hook_path(git_repo)
    assert path.is_file()
    assert path.stat().st_mode & 0o111
    assert hooks.MARKER in path.read_text()


def test_install_is_idempotent_over_its_own_hook(git_repo):
    main(["hooks", "install", "--root", str(git_repo)])
    assert main(["hooks", "install", "--root", str(git_repo)]) == 0


def test_force_replaces_a_foreign_hook(git_repo):
    path = hooks.hook_path(git_repo)
    path.write_text("#!/bin/sh\necho foreign\n")
    assert main(["hooks", "install", "--root", str(git_repo), "--force"]) == 0
    assert hooks.MARKER in path.read_text()


def test_uninstall_leaves_a_foreign_hook_alone(git_repo, capsys):
    path = hooks.hook_path(git_repo)
    path.write_text("#!/bin/sh\necho foreign\n")
    assert main(["hooks", "uninstall", "--root", str(git_repo)]) == 2
    assert "foreign" in path.read_text()


def test_uninstall_removes_its_own_hook(git_repo):
    main(["hooks", "install", "--root", str(git_repo)])
    assert main(["hooks", "uninstall", "--root", str(git_repo)]) == 0
    assert not hooks.hook_path(git_repo).exists()


def test_status_reports_each_case(git_repo, capsys):
    main(["hooks", "status", "--root", str(git_repo)])
    assert "not installed" in capsys.readouterr().out
    main(["hooks", "install", "--root", str(git_repo)])
    main(["hooks", "status", "--root", str(git_repo)])
    assert "installed by amigos" in capsys.readouterr().out


def test_install_outside_a_git_repository_reports_a_problem(tmp_path, capsys):
    assert main(["hooks", "install", "--root", str(tmp_path)]) == 2
    assert "not a git repository" in capsys.readouterr().out


def test_the_installed_hook_blocks_a_real_commit(git_repo):
    """End to end: git itself refuses the commit."""
    main(["hooks", "install", "--root", str(git_repo)])
    (git_repo / "src_new.py").write_text("x = 1\n")
    subprocess.run(["git", "add", "src_new.py"], cwd=git_repo, check=True)

    result = subprocess.run(
        ["git", "commit", "-m", "change a governed file"],
        cwd=git_repo, capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "refused" in (result.stderr + result.stdout)


def test_the_installed_hook_allows_a_commit_touching_only_exempt_paths(git_repo):
    main(["hooks", "install", "--root", str(git_repo)])
    (git_repo / "docs").mkdir(exist_ok=True)
    (git_repo / "docs" / "note.md").write_text("a note\n")
    subprocess.run(["git", "add", "docs/note.md"], cwd=git_repo, check=True)

    result = subprocess.run(
        ["git", "commit", "-m", "docs only"], cwd=git_repo, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr


def test_the_installed_hook_allows_a_governed_commit_under_a_ready_story(git_repo):
    main(["hooks", "install", "--root", str(git_repo)])
    (git_repo / ".amigos" / "ACTIVE").write_text("READY-001\n")
    (git_repo / "src_new.py").write_text("x = 1\n")
    subprocess.run(["git", "add", "src_new.py"], cwd=git_repo, check=True)

    result = subprocess.run(
        ["git", "commit", "-m", "governed, under a ready story"],
        cwd=git_repo, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr + result.stdout
