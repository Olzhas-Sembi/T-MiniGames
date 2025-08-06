#!/usr/bin/env python3
"""
Скрипт для тестирования CORS настроек локально
"""

import requests
import sys

def test_cors():
    """Тестируем CORS с локальным сервером"""
    base_url = "http://localhost:8000"
    
    # Тестируем OPTIONS запрос
    print("🔍 Тестируем OPTIONS запрос...")
    try:
        response = requests.options(
            f"{base_url}/api/news",
            headers={
                "Origin": "https://rustembekov.github.io",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        print(f"✅ OPTIONS статус: {response.status_code}")
        print(f"📋 CORS заголовки:")
        for header, value in response.headers.items():
            if header.lower().startswith('access-control'):
                print(f"   {header}: {value}")
        print()
    except Exception as e:
        print(f"❌ Ошибка OPTIONS: {e}")
        print()

    # Тестируем GET запрос
    print("🔍 Тестируем GET запрос...")
    try:
        response = requests.get(
            f"{base_url}/api/news",
            headers={
                "Origin": "https://rustembekov.github.io"
            }
        )
        print(f"✅ GET статус: {response.status_code}")
        print(f"📋 CORS заголовки:")
        for header, value in response.headers.items():
            if header.lower().startswith('access-control'):
                print(f"   {header}: {value}")
        print()
    except Exception as e:
        print(f"❌ Ошибка GET: {e}")
        print()

def test_render_cors():
    """Тестируем CORS с Render сервером"""
    base_url = "https://t-minigames.onrender.com"
    
    print("🌐 Тестируем CORS на Render...")
    
    # Тестируем OPTIONS запрос
    print("🔍 Тестируем OPTIONS запрос...")
    try:
        response = requests.options(
            f"{base_url}/api/news",
            headers={
                "Origin": "https://rustembekov.github.io",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type"
            },
            timeout=10
        )
        print(f"✅ OPTIONS статус: {response.status_code}")
        print(f"📋 CORS заголовки:")
        for header, value in response.headers.items():
            if header.lower().startswith('access-control'):
                print(f"   {header}: {value}")
        print()
    except Exception as e:
        print(f"❌ Ошибка OPTIONS: {e}")
        print()

    # Тестируем GET запрос
    print("🔍 Тестируем GET запрос...")
    try:
        response = requests.get(
            f"{base_url}/api/news",
            headers={
                "Origin": "https://rustembekov.github.io"
            },
            timeout=10
        )
        print(f"✅ GET статус: {response.status_code}")
        print(f"📋 CORS заголовки:")
        for header, value in response.headers.items():
            if header.lower().startswith('access-control'):
                print(f"   {header}: {value}")
        print()
    except Exception as e:
        print(f"❌ Ошибка GET: {e}")
        print()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "local":
        test_cors()
    else:
        test_render_cors()
