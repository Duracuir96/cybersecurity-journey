# test_java_sales_client.py
import asyncio
import os
from dotenv import load_dotenv

from src.clients.java_sales_client import JavaSalesClient
from src.api.settings import DEV_MODE

# --------------------------------------------------
# ENV
# --------------------------------------------------
load_dotenv()


async def test_java_sales_client():
    print("\n" + "=" * 60)
    print("🧪 TEST — JavaSalesClient (RAW DATA)")
    print("=" * 60)

    print(f"JAVA_API_URL = {os.getenv('JAVA_API_URL')}")
    print(f"DEV_MODE     = {DEV_MODE}")

    token = os.getenv("JAVA_API_TOKEN")  # optionnel
    client = JavaSalesClient(token=token)

    try:
        # --------------------------------------------------
        # 1️⃣ RECENT SALES
        # --------------------------------------------------
        print("\n📌 1. get_recent_sales()")

        try:
            recent_sales = await client.get_recent_sales()
            print(f"✅ OK — {len(recent_sales)} ventes récupérées")

            if recent_sales:
                s = recent_sales[0]
                print("   Exemple vente :")
                print(f"   - saleId     = {s.saleId}")
                print(f"   - saleDate   = {s.saleDate}")
                print(f"   - totalAmount = {s.totalAmount}")
                print(f"   - items      = {len(s.items)}")
        except Exception as e:
            print(f"❌ ERREUR recent_sales: {e}")

        # --------------------------------------------------
        # 2️⃣ SALES HISTORY (GLOBAL)
        # --------------------------------------------------
        print("\n📌 2. get_sales_history()")

        try:
            history = await client.get_sales_history()
            print(f"✅ OK — {len(history)} ventes dans l'historique")

            if history:
                s = history[0]
                print("   Exemple historique :")
                print(f"   - saleId     = {s.saleId}")
                print(f"   - saleDate   = {s.saleDate}")
                print(f"   - totalAmount = {s.totalAmount}")
        except Exception as e:
            print(f"❌ ERREUR history: {e}")

        # --------------------------------------------------
        # 3️⃣ SALES HISTORY BY SKU (ML PRODUCT)
        # --------------------------------------------------
        print("\n📌 3. get_sales_history_by_sku('SUGAR-003')")

        try:
            sku_history = await client.get_sales_history_by_sku("SUGAR-003")
            print(f"✅ OK — {len(sku_history)} points pour ce SKU")

            if sku_history:
                p = sku_history[0]
                print("   Exemple point ML :")
                print(f"   - date     = {p.date}")
                print(f"   - quantity = {p.quantity}")
        except Exception as e:
            print(f"⚠️ SKU non trouvé ou vide: {e}")

        # --------------------------------------------------
        # 4️⃣ SALES HISTORY BY NAME (OPTION UI)
        # --------------------------------------------------
        print("\n📌 4. get_sales_history_by_name('Sugar')")

        try:
            name_history = await client.get_sales_history_by_name("Sugar")
            print(f"✅ OK — {len(name_history)} points pour ce produit")

            if name_history:
                p = name_history[0]
                print("   Exemple point :")
                print(f"   - date     = {p.date}")
                print(f"   - quantity = {p.quantity}")
        except Exception as e:
            print(f"⚠️ Name non trouvé ou vide: {e}")

    finally:
        await client.close()

    print("\n" + "=" * 60)
    print("✅ TEST TERMINÉ")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_java_sales_client())
