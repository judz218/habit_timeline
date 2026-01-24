# Habit Timeline CLI

## 概要

タスクをテンプレートとして登録し、指定日のタイムラインに展開できる CLI アプリケーション。

## できること

- タスクの追加
- 手順の追加
- 日付ごとの計画作成
- タスクをタイムラインに展開
- 完了管理

## 使い方

### コマンド一覧

```
python app.py --help
```

### データベースの初期化

```
python app.py init
```

### タスクテンプレート

- タスクの登録

```
python app.py habit-add "タスク名(例:歯磨き)" "最初の一手(洗面所に行く)"
```

- 手順の登録

```
python app.py step-add 1 "洗面所に行く" --sort-order 1
python app.py step-add 1 "歯ブラシに歯磨き粉をつける" --sort-order 2
python app.py step-add 1 "磨く" --sort-order 3
```

- タスク一覧を表示

```
python app.py habit-list
```

- タスクを指定して手順を表示

```
python app.py step-list タスクのid
### 計画作成

- 日付ごとの作成

```

python app.py plan-init YYYY-MM-DD

```

- タイムラインに加える

```

python app.py plan-add-habit YYYY-MM-DD タスクid --time hh:mm

```

- タイムラインの表示

```

python app.py plan-show YYYY-MM-DD

```

- タスク完了

```

python app.py plan-done タイムライン上のid

```

```
