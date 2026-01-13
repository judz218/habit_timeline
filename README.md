# Habit Timeline CLI

## 概要

習慣をテンプレートとして登録し、指定日のタイムラインに展開できる CLI アプリケーション。

## できること

- 習慣の追加
- 手順の追加
- 日付ごとの計画作成
- 習慣をタイムラインに展開
- 完了管理

## 使い方

### データベースの初期化

一番最初に一度だけ行ってください。

```
python app.py init
```

### 習慣テンプレート

習慣の登録

```
python app.py habit-add "習慣名(例:歯磨き)" "最初の一手(洗面所に行く)"
```

手順の登録

```
python app.py step-add 1 "洗面所に行く" --sort-order 1
python app.py step-add 1 "歯ブラシに歯磨き粉をつける" --sort-order 2
python app.py step-add 1 "磨く" --sort-order 3
```

一覧を表示

```
python app.py habit_list
```

### 日付ごとの計画作成

```
python app.py plan-init 2026-01-13
```

### タイムライン

タイムラインに加える

```
python app.py plan-add-habit 2026-01-13 1 --time 07:30
```

タイムラインの表示

```
python app.py plan-show 2026-01-13
```

タスク完了

```
python app.py plan-done 3
```
