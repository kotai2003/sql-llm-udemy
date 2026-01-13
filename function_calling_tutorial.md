Summary:

このコードは **「LLM（ChatGPT）に、必要なら関数を呼び出させて、その結果をもう一度LLMに渡して最終回答を作らせる」** という **Function Calling（Tool Calling）** の最小構成サンプルです。

流れはこうです：

1. ユーザーが質問する
2. LLMが「この質問は関数で調べた方がいい」と判断したら **tool_calls** を返す（＝関数呼び出し指示）
3. Python側が実際に関数を実行して結果を得る
4. その結果を「toolメッセージ」として会話に追加
5. LLMに再度投げて、最終的な自然文回答を作らせる

---

## 1. このコードの目的（何をしている？）

ユーザーがこう聞きます：

> San Francisco, Tokyo, Paris の天気は？

普通にLLMに聞くと「それっぽく答える」可能性があります。
でも Function Calling を使うと、

* LLMは **勝手に天気を捏造せず**
* 「天気取得関数を呼んでください」という指示を出し
* あなたのPythonが **本当に取得した結果** を渡して
* 最終回答を生成できます

このコードでは天気APIの代わりに、ダミー関数 `get_current_weather()` が固定値を返しています。

---

## 2. 重要な登場人物

### (A) `get_current_weather()` ← “あなた側の関数”

```python
def get_current_weather(location, unit="fahrenheit"):
```

これは **LLMが実行する関数ではありません**。
LLMは「呼び出して」と言うだけで、実際に動かすのはPythonです。

返り値が `json.dumps(...)` になっているのがポイントで、
LLMに渡す結果が **JSON文字列** になっています。

例：San Franciscoなら

```json
{"location":"San Francisco","temperature":"72","unit":"fahrenheit"}
```

---

### (B) `tools` ← “LLMに見せる関数仕様書”

ここが function calling の心臓です。

```python
tools = [
  {
    "type": "function",
    "function": {
      "name": "get_current_weather",
      "description": "...",
      "parameters": {...}
    }
  }
]
```

これは「こういう関数が使えますよ」という **API仕様書（schema）** をLLMに渡しています。

特に重要なのが `parameters` です。

```python
"parameters": {
  "type": "object",
  "properties": {
    "location": {"type": "string"},
    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
  },
  "required": ["location"]
}
```

意味はこうです：

* 引数はオブジェクト（JSON）で渡してね
* `location` は文字列で必須
* `unit` は `"celsius"` or `"fahrenheit"` のどっちか

LLMはこれを見て「正しい引数の形」を作ろうとします。

---

### (C) `client.chat.completions.create(...)` ← “LLMに質問する”

最初の呼び出しはこれです：

```python
response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=tools,
    tool_choice="auto",
)
```

ここでLLMは

* 普通に文章で答えるか
* `get_current_weather()` を呼ぶべきか

を判断します。

`tool_choice="auto"` は「LLMが必要なら呼ぶ」を意味します。

---

## 3. Function Calling の本体の流れ（超重要）

### Step 1: まず普通に質問する

```python
messages = [{"role": "user", "content": "..."}]
```

---

### Step 2: LLMの返答を見る

```python
response_message = response.choices[0].message
tool_calls = response_message.tool_calls
```

ここで `tool_calls` が **空なら**
→ LLMは「関数呼ばなくていい」と判断した

`tool_calls` が **入っていたら**
→ LLMは「関数呼んで」と判断した

---

### Step 3: tool_calls があったら、Pythonで関数実行する

```python
function_args = json.loads(tool_call.function.arguments)
function_response = function_to_call(
    location=function_args.get("location"),
    unit=function_args.get("unit"),
)
```

ここで初心者が混乱しやすい点：

* `tool_call.function.arguments` は **文字列(JSON)** で返ってきます
  なので `json.loads()` で dict にします。

例えばLLMがこう返してきたとします：

```json
{"location":"Tokyo","unit":"fahrenheit"}
```

それをPythonで実行します。

---

### Step 4: 関数の結果を messages に追加する（role="tool"）

ここが最大のポイントです。

```python
messages.append({
  "tool_call_id": tool_call.id,
  "role": "tool",
  "name": function_name,
  "content": function_response,
})
```

意味は：

* 「この tool_call_id の関数を実行しました」
* 「結果はこれです」

という証拠を会話ログに足す感じです。

これをやらないと、LLMは **関数結果を見れません**。

---

### Step 5: もう一度LLMに投げて、最終回答を作らせる

```python
second_response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
)
```

ここでは tools を渡してないですがOKです。
なぜならもう「結果を文章化するだけ」だからです。

---

## 4. このコードの出力は何？

最後にこれを print しています：

```python
print(run_conversation().model_dump_json(indent=2))
```

つまり「2回目のLLM応答（最終回答）」が JSON で表示されます。

---

## 5. 初心者がハマるポイント（ここだけ押さえればOK）

### (1) LLMは関数を実行しない

LLMは「呼びたい」と言うだけ。
実行はあなたのPython。

---

### (2) tool_calls が返ってくるのは “指示”

例：「Tokyoの天気を get_current_weather で調べて」

---

### (3) tool の結果を messages に入れないと、LLMは知らないまま

`role="tool"` の messages が超重要。

---

### (4) tool_call_id が必要

これがないと「どの関数呼び出しに対する結果か」が対応できません。

---

## 6. あなたのコードで気になる点（改善候補）

### (A) LangChain の `ChatOpenAI` は作ってるけど使ってない

```python
model = ChatOpenAI(...)
```

この `model` は以降使われていません。

このサンプルは **OpenAI公式SDK方式** で function calling しているので、
LangChain部分は削除してOKです（混乱防止）。

---

### (B) `get_current_weather()` はJSON文字列を返している

これは良い設計です。
Tool結果は「文字列」で渡す必要があるので、JSON文字列が扱いやすいです。

---

### (C) location が3都市なので tool_calls が複数回出る

ユーザーが3都市を聞いているので、LLMはたぶんこうします：

* San Franciscoで1回
* Tokyoで1回
* Parisで1回

つまり `tool_calls` は複数になることが多いです。

このコードはちゃんと `for tool_call in tool_calls:` で対応できています。

---

## 7. このコードを一言でいうと？

**「LLMが“必要なら関数呼んでね”と言う → Pythonが関数実行 → 結果を渡す → LLMが自然文でまとめる」**
これが Function Calling です。

---

Citations:

• [OpenAI API Docs, Function Calling / Tools, 2024]
• Source unavailable (提示コードは一般的なFunction Callingの構成に一致)
