print("🔍 Simple Import Test\n")

# Test 1
try:
    import whisper
    print("✅ Whisper imported")
except Exception as e:
    print(f"❌ Whisper: {e}")

# Test 2
try:
    import google.generativeai
    print("✅ Gemini imported")
except Exception as e:
    print(f"❌ Gemini: {e}")

# Test 3
try:
    from supabase import create_client
    print("✅ Supabase imported")
except Exception as e:
    print(f"❌ Supabase: {e}")

# Test 4
try:
    from dotenv import load_dotenv
    import os
    load_dotenv()
    
    gemini = os.getenv("GEMINI_API_KEY")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if gemini:
        print(f"✅ GEMINI_API_KEY found ({gemini[:20]}...)")
    else:
        print("❌ GEMINI_API_KEY not found in .env")
    
    if supabase_url:
        print(f"✅ SUPABASE_URL found ({supabase_url})")
    else:
        print("❌ SUPABASE_URL not found in .env")
    
    if supabase_key:
        print(f"✅ SUPABASE_KEY found ({supabase_key[:30]}...)")
    else:
        print("❌ SUPABASE_KEY not found in .env")
        
except Exception as e:
    print(f"❌ Environment check: {e}")

print("\n✨ Test complete!")