import httpx
from supabase import create_client
import os
from typing import Sequence, Dict, Any

from dotenv import load_dotenv

load_dotenv()

# Supabase クライアント
try:
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    timeout = httpx.Timeout(30.0)  # 30秒に設定
    #supabase = create_client(SUPABASE_URL, SUPABASE_KEY, options={"timeout": timeout})
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase クライアント作成成功")
except Exception as e:
    print(f"❌ Supabase 接続エラー: {e}")
    supabase = None

# データの挿入
def insert_data(message_id, command_id):
    if supabase is None:
        print("⚠️ Supabase 未接続のためデータを挿入できません")
        return
    try:
        supabase.table("help_id").insert({
            "message_id": str(message_id),
            "command_id": str(command_id)
        }).execute()
        #print(f"✅ データが挿入されました: message_id={message_id}, command_id={command_id}")
    except Exception as e:
        print(f"❌ データ挿入エラー: {e}")

# データの取得
def get_data() -> Sequence[Dict[str, Any]]:
    if supabase is None:
        print("⚠️ Supabase 未接続")
        return []

    response = supabase.table("help_id").select("*").order("id").execute()
    data = response.data or []

    # None の場合に空リストに置き換える
    rows: Sequence[Dict[str, Any]] = [row for row in data if isinstance(row, dict)]

    for row in rows:
        if not isinstance(row, dict):
            continue  # dict でない場合はスキップ
        #message_id = row.get("message_id")
        #command_id = row.get("command_id")
        #print(f"message_id={message_id}, command_id={command_id}")

    return rows


# メッセージデータの削除
def delete_data(message_id):
    if supabase is None:
        print("⚠️ Supabase 未接続のためデータを削除できません")
        return
    try:
        supabase.table("help_id").delete().eq("message_id", str(message_id)).execute()
        #print(f"🗑 データが削除されました: message_id={message_id}")
    except Exception as e:
        print(f"❌ データ削除エラー: {e}")

# コマンドデータの削除
def delete_command_data(command_id):
    if supabase is None:
        print("⚠️ Supabase 未接続のためデータを削除できません")
        return
    try:
        supabase.table("help_id").delete().eq("command_id", str(command_id)).execute()
        #print(f"🗑 データが削除されました: command_id={command_id}")
    except Exception as e:
        print(f"❌ データ削除エラー: {e}")
