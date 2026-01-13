from __future__ import annotations

from datetime import date
import re
import typer
from rich.console import Console
from rich.table import Table

import db as dbmod

app = typer.Typer(add_completion=False)
console = Console()

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIME_RE = re.compile(r"^\d{2}:\d{2}$")


def validate_date(s: str) -> str:
    if not DATE_RE.match(s):
        raise typer.BadParameter("YYYY-MM-DD 形式で指定してください")
    return s


def validate_time_or_none(s: str | None) -> str | None:
    if s is None:
        return None
    if not TIME_RE.match(s):
        raise typer.BadParameter("HH:MM 形式で指定してください（例 07:30）")
    hh, mm = map(int, s.split(":"))
    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        raise typer.BadParameter("時刻が不正です")
    return s


@app.command()
def init():
    """DBを初期化（app.db を作成）"""
    dbmod.init_db()
    console.print("[green]DB initialized:[/green] app.db")


@app.command()
def habit_add(name: str, first_action: str):
    """習慣テンプレを追加"""
    dbmod.init_db()
    conn = dbmod.connect()
    try:
        hid = dbmod.execute(
            conn,
            "INSERT INTO habit(name, first_action) VALUES (?, ?)",
            (name, first_action),
        )
        conn.commit()
        console.print(f"[green]Added habit[/green] id={hid} name={name}")
    finally:
        conn.close()


@app.command()
def habit_list():
    """習慣テンプレ一覧"""
    dbmod.init_db()
    conn = dbmod.connect()
    try:
        rows = dbmod.fetch_all(conn, "SELECT id, name, first_action, created_at FROM habit ORDER BY id")
        table = Table(title="Habits")
        table.add_column("id", justify="right")
        table.add_column("name")
        table.add_column("first_action")
        table.add_column("created_at")
        for r in rows:
            table.add_row(str(r["id"]), r["name"], r["first_action"], r["created_at"])
        console.print(table)
    finally:
        conn.close()


@app.command()
def step_add(habit_id: int, title: str, sort_order: int = 1, parent_step_id: int | None = None):
    """習慣に手順（ステップ）を追加（親子も可）"""
    dbmod.init_db()
    conn = dbmod.connect()
    try:
        habit = dbmod.fetch_one(conn, "SELECT id FROM habit WHERE id=?", (habit_id,))
        if habit is None:
            raise typer.BadParameter(f"habit_id={habit_id} は存在しません")

        if parent_step_id is not None:
            parent = dbmod.fetch_one(
                conn, "SELECT id, habit_id FROM habit_step WHERE id=?", (parent_step_id,)
            )
            if parent is None:
                raise typer.BadParameter(f"parent_step_id={parent_step_id} は存在しません")
            if int(parent["habit_id"]) != habit_id:
                raise typer.BadParameter("親ステップが別の習慣に属しています")

        sid = dbmod.execute(
            conn,
            "INSERT INTO habit_step(habit_id, parent_step_id, title, sort_order) VALUES (?, ?, ?, ?)",
            (habit_id, parent_step_id, title, sort_order),
        )
        conn.commit()
        console.print(f"[green]Added step[/green] id={sid} habit_id={habit_id} title={title}")
    finally:
        conn.close()


@app.command()
def step_list(habit_id: int):
    """習慣の手順一覧（階層はインデント表示）"""
    dbmod.init_db()
    conn = dbmod.connect()
    try:
        rows = dbmod.fetch_all(
            conn,
            """
            SELECT id, habit_id, parent_step_id, title, sort_order
            FROM habit_step
            WHERE habit_id=?
            ORDER BY parent_step_id IS NOT NULL, parent_step_id, sort_order, id
            """,
            (habit_id,),
        )

        # build tree
        by_parent: dict[int | None, list[dict]] = {}
        for r in rows:
            by_parent.setdefault(r["parent_step_id"], []).append(
                {"id": r["id"], "title": r["title"], "sort_order": r["sort_order"]}
            )

        table = Table(title=f"Habit Steps (habit_id={habit_id})")
        table.add_column("id", justify="right")
        table.add_column("title")

        def dfs(parent: int | None, depth: int):
            for node in sorted(by_parent.get(parent, []), key=lambda x: (x["sort_order"], x["id"])):
                table.add_row(str(node["id"]), "  " * depth + node["title"])
                dfs(node["id"], depth + 1)

        dfs(None, 0)
        console.print(table)
    finally:
        conn.close()


@app.command()
def plan_init(plan_date: str = typer.Argument(default=str(date.today()), callback=validate_date)):
    """指定日(YYYY-MM-DD)の計画を作成（なければ作る）"""
    dbmod.init_db()
    conn = dbmod.connect()
    try:
        existing = dbmod.fetch_one(conn, "SELECT id FROM day_plan WHERE plan_date=?", (plan_date,))
        if existing is not None:
            console.print(f"[yellow]Already exists[/yellow] plan_date={plan_date}")
            return
        pid = dbmod.execute(conn, "INSERT INTO day_plan(plan_date) VALUES (?)", (plan_date,))
        conn.commit()
        console.print(f"[green]Created plan[/green] id={pid} date={plan_date}")
    finally:
        conn.close()


def _get_plan_id(conn, plan_date: str) -> int:
    row = dbmod.fetch_one(conn, "SELECT id FROM day_plan WHERE plan_date=?", (plan_date,))
    if row is None:
        raise typer.BadParameter(f"plan_date={plan_date} の計画がありません。plan_init を先に実行してください。")
    return int(row["id"])


@app.command()
def plan_add_habit(
    plan_date: str = typer.Argument(..., callback=validate_date),
    habit_id: int = typer.Argument(...),
    scheduled_time: str | None = typer.Option(None, "--time", callback=validate_time_or_none),
):
    """指定日のタイムラインに習慣を展開追加（習慣 + その手順を複製）"""
    dbmod.init_db()
    conn = dbmod.connect()
    try:
        day_plan_id = _get_plan_id(conn, plan_date)

        habit = dbmod.fetch_one(conn, "SELECT id, name, first_action FROM habit WHERE id=?", (habit_id,))
        if habit is None:
            raise typer.BadParameter(f"habit_id={habit_id} は存在しません")

        # 現在の最大 sort_order を取得し、その後ろに追加
        last = dbmod.fetch_one(
            conn,
            "SELECT COALESCE(MAX(sort_order), 0) AS mx FROM plan_item WHERE day_plan_id=?",
            (day_plan_id,),
        )
        base_order = int(last["mx"]) + 1

        # 1) まず習慣本体を追加
        habit_item_id = dbmod.execute(
            conn,
            """
            INSERT INTO plan_item(day_plan_id, title, scheduled_time, sort_order, source_habit_id, source_step_id)
            VALUES (?, ?, ?, ?, ?, NULL)
            """,
            (day_plan_id, f"[習慣] {habit['name']} / 最初: {habit['first_action']}", scheduled_time, base_order, habit_id),
        )

        # 2) 次にトップレベルのステップを順序順に展開
        steps = dbmod.fetch_all(
            conn,
            """
            SELECT id, title, sort_order
            FROM habit_step
            WHERE habit_id=? AND parent_step_id IS NULL
            ORDER BY sort_order, id
            """,
            (habit_id,),
        )

        order = base_order + 1
        for s in steps:
            dbmod.execute(
                conn,
                """
                INSERT INTO plan_item(
                day_plan_id, title, scheduled_time, sort_order,
                source_habit_id, source_step_id, parent_item_id
                )
                VALUES (?, ?, NULL, ?, ?, ?, ?)
                """,
                (day_plan_id, f"  - {s['title']}", order, habit_id, int(s["id"]), habit_item_id),
            )
            order += 1

        conn.commit()
        console.print(f"[green]Added habit to plan[/green] date={plan_date} habit_id={habit_id} (+{1+len(steps)} items)")
        console.print(f"habit_item_id={habit_item_id}")
    finally:
        conn.close()


@app.command()
def plan_show(plan_date: str = typer.Argument(..., callback=validate_date)):
    """指定日のタイムライン表示"""
    dbmod.init_db()
    conn = dbmod.connect()
    try:
        day_plan_id = _get_plan_id(conn, plan_date)
        rows = dbmod.fetch_all(
            conn,
            """
            SELECT
            pi.id,
            pi.title,
            pi.scheduled_time,
            pi.sort_order,
            pi.done_at,
            COALESCE(p.scheduled_time, pi.scheduled_time) AS effective_time,
            COALESCE(pi.parent_item_id, pi.id) AS group_id
            FROM plan_item pi
            LEFT JOIN plan_item p ON p.id = pi.parent_item_id
            WHERE pi.day_plan_id=?
            ORDER BY
            CASE WHEN effective_time IS NULL THEN 1 ELSE 0 END,
            effective_time,
            group_id,
            pi.sort_order,
            pi.id
            """,
            (day_plan_id,),
        )
        table = Table(title=f"Timeline {plan_date}")
        table.add_column("id", justify="right")
        table.add_column("time", justify="center")
        table.add_column("title")
        table.add_column("done", justify="center")

        for r in rows:
            done = "✅" if r["done_at"] is not None else ""
            tm = r["scheduled_time"] or ""
            table.add_row(str(r["id"]), tm, r["title"], done)

        console.print(table)
    finally:
        conn.close()


@app.command()
def plan_done(item_id: int):
    """タイムライン項目を完了にする"""
    dbmod.init_db()
    conn = dbmod.connect()
    try:
        row = dbmod.fetch_one(conn, "SELECT id, done_at FROM plan_item WHERE id=?", (item_id,))
        if row is None:
            raise typer.BadParameter(f"item_id={item_id} は存在しません")
        if row["done_at"] is not None:
            console.print("[yellow]Already done[/yellow]")
            return
        conn.execute("UPDATE plan_item SET done_at=datetime('now') WHERE id=?", (item_id,))
        conn.commit()
        console.print(f"[green]Done[/green] item_id={item_id}")
    finally:
        conn.close()


if __name__ == "__main__":
    app()
