# -*- coding: utf-8 -*-
"""
Пример использования API Dellin для расчета стоимости доставки
Интеграция с методичкой расчета стоимости монтажных работ
"""

import requests
import json
from datetime import datetime, timedelta
from pathlib import Path

# Ключ приложения Dellin
APPKEY = "433D67A0-A9D1-4293-A14C-83329023A30F"

# Базовый URL API
API_BASE_URL = "https://api.dellin.ru/v2/"

class DellinCalculator:
    """Класс для работы с API Dellin калькулятора стоимости доставки"""
    
    def __init__(self, appkey):
        self.appkey = appkey
        self.session = requests.Session()
    
    def find_city(self, city_name):
        """
        Поиск города по названию для получения кода КЛАДР
        
        Args:
            city_name: Название города (например, "Екатеринбург")
            
        Returns:
            dict: Информация о городе с кодом КЛАДР
        """
        url = f"{API_BASE_URL}cities.json"
        payload = {
            "appkey": self.appkey,
            "q": city_name
        }
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if data.get("success") and data.get("cities"):
                # Возвращаем первый найденный город
                return data["cities"][0]
            else:
                return None
        except Exception as e:
            print(f"Ошибка при поиске города: {e}")
            return None
    
    def calculate_cost(self, 
                       from_city_code, 
                       to_city_code,
                       weight_kg,
                       length_cm=None,
                       width_cm=None,
                       height_cm=None,
                       volume_m3=None,
                       delivery_date=None,
                       pickup_date=None,
                       terminal_from=None,
                       terminal_to=None,
                       address_from=None,
                       address_to=None):
        """
        Расчет стоимости доставки
        
        Args:
            from_city_code: Код КЛАДР города отправки
            to_city_code: Код КЛАДР города получения
            weight_kg: Вес груза в кг
            length_cm: Длина в см (опционально)
            width_cm: Ширина в см (опционально)
            height_cm: Высота в см (опционально)
            volume_m3: Объем в м³ (опционально, вычисляется из габаритов)
            delivery_date: Дата доставки (YYYY-MM-DD) или None для ближайшей
            pickup_date: Дата забора (YYYY-MM-DD) или None для ближайшей
            terminal_from: ID терминала отправки (если variant=terminal)
            terminal_to: ID терминала получения (если variant=terminal)
            address_from: Адрес забора (если variant=address)
            address_to: Адрес доставки (если variant=address)
            
        Returns:
            dict: Результат расчета с стоимостью и сроками
        """
        url = f"{API_BASE_URL}calculator.json"
        
        # Определение варианта доставки
        if terminal_from:
            derival_variant = "terminal"
            derival_terminal = terminal_from
        else:
            derival_variant = "address"
            derival_address = address_from or ""
        
        if terminal_to:
            arrival_variant = "terminal"
            arrival_terminal = terminal_to
        else:
            arrival_variant = "address"
            arrival_address = address_to or ""
        
        # Вычисление объема из габаритов, если не указан
        if not volume_m3 and length_cm and width_cm and height_cm:
            volume_m3 = (length_cm * width_cm * height_cm) / 1_000_000  # м³
        
        # Дата забора (по умолчанию сегодня + 1 день)
        if not pickup_date:
            pickup_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Дата доставки (по умолчанию сегодня + 5 дней)
        if not delivery_date:
            delivery_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        
        # Формирование запроса
        payload = {
            "appkey": self.appkey,
            "delivery": {
                "deliveryType": {
                    "type": "auto"
                },
                "arrival": {
                    "variant": arrival_variant,
                    "produceDate": delivery_date
                },
                "derival": {
                    "variant": derival_variant,
                    "produceDate": pickup_date
                }
            },
            "cargo": {
                "quantity": 1,
                "weight": weight_kg,
                "totalWeight": weight_kg
            }
        }
        
        # Добавление параметров города
        payload["delivery"]["arrival"]["city"] = to_city_code
        payload["delivery"]["derival"]["city"] = from_city_code
        
        # Добавление габаритов
        if length_cm:
            payload["cargo"]["length"] = length_cm
        if width_cm:
            payload["cargo"]["width"] = width_cm
        if height_cm:
            payload["cargo"]["height"] = height_cm
        if volume_m3:
            payload["cargo"]["totalVolume"] = volume_m3
        
        # Добавление терминалов или адресов
        if terminal_from:
            payload["delivery"]["derival"]["terminalID"] = terminal_from
        elif address_from:
            payload["delivery"]["derival"]["address"] = address_from
        
        if terminal_to:
            payload["delivery"]["arrival"]["terminalID"] = terminal_to
        elif address_to:
            payload["delivery"]["arrival"]["address"] = address_to
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            return data
        except Exception as e:
            print(f"Ошибка при расчете стоимости: {e}")
            print(f"Ответ сервера: {response.text if 'response' in locals() else 'Нет ответа'}")
            return None


def calculate_logistics_cost(equipment_list, from_city, to_city):
    """
    Расчет стоимости логистики для списка оборудования
    
    Args:
        equipment_list: Список словарей с параметрами оборудования:
            [{"name": "LED-экран", "weight": 4104, "length": 900, "width": 1200, "height": 50}]
        from_city: Город отправки
        to_city: Город получения
        
    Returns:
        dict: Результат расчета с детализацией
    """
    calculator = DellinCalculator(APPKEY)
    
    # Поиск кодов городов
    from_city_data = calculator.find_city(from_city)
    to_city_data = calculator.find_city(to_city)
    
    if not from_city_data or not to_city_data:
        return {
            "error": "Не удалось найти один из городов",
            "from_city_data": from_city_data,
            "to_city_data": to_city_data
        }
    
    from_city_code = from_city_data["code"]
    to_city_code = to_city_data["code"]
    
    # Суммарные параметры груза
    total_weight = sum(eq.get("weight", 0) for eq in equipment_list)
    total_volume = sum(
        (eq.get("length", 0) * eq.get("width", 0) * eq.get("height", 0)) / 1_000_000
        for eq in equipment_list
        if all(k in eq for k in ["length", "width", "height"])
    )
    
    # Максимальные габариты
    max_length = max((eq.get("length", 0) for eq in equipment_list), default=0)
    max_width = max((eq.get("width", 0) for eq in equipment_list), default=0)
    max_height = max((eq.get("height", 0) for eq in equipment_list), default=0)
    
    # Расчет стоимости
    result = calculator.calculate_cost(
        from_city_code=from_city_code,
        to_city_code=to_city_code,
        weight_kg=total_weight,
        length_cm=max_length,
        width_cm=max_width,
        height_cm=max_height,
        volume_m3=total_volume
    )
    
    return {
        "from_city": from_city,
        "to_city": to_city,
        "from_city_code": from_city_code,
        "to_city_code": to_city_code,
        "total_weight_kg": total_weight,
        "total_volume_m3": total_volume,
        "max_dimensions": {
            "length": max_length,
            "width": max_width,
            "height": max_height
        },
        "calculation_result": result,
        "calculation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": f"API Dellin (appkey: {APPKEY[:8]}...)",
    }


# Пример использования
if __name__ == "__main__":
    # Пример расчета для LED-экрана 9×12м
    equipment = [
        {
            "name": "LED-экран 9×12м",
            "weight": 4104,  # кг
            "length": 900,   # см
            "width": 1200,   # см
            "height": 50     # см
        },
        {
            "name": "Оборудование механики подъема",
            "weight": 500,   # кг
            "length": 300,   # см
            "width": 200,    # см
            "height": 150    # см
        }
    ]
    
    result = calculate_logistics_cost(
        equipment_list=equipment,
        from_city="Екатеринбург",
        to_city="Москва"
    )
    
    print("=" * 70)
    print("РАСЧЕТ СТОИМОСТИ ДОСТАВКИ ЧЕРЕЗ API DELLIN")
    print("=" * 70)
    print(f"\nМаршрут: {result['from_city']} → {result['to_city']}")
    print(f"Общий вес: {result['total_weight_kg']} кг")
    print(f"Общий объем: {result['total_volume_m3']:.3f} м³")
    print(f"Источник: {result['source']}")
    print(f"Дата расчета: {result['calculation_date']}")
    
    if result.get("calculation_result"):
        calc_data = result["calculation_result"]
        if calc_data.get("success"):
            prices = calc_data.get("price", {})
            print(f"\n✓ Расчет выполнен успешно")
            print(f"  Стоимость доставки: {prices.get('delivery', 'N/A')} руб")
            print(f"  Срок доставки: {calc_data.get('time', {}).get('delivery', 'N/A')} дней")
        else:
            print(f"\n✗ Ошибка при расчете:")
            print(f"  {calc_data.get('errors', [])}")
    else:
        print("\n✗ Не удалось получить результат расчета")
    
    print("\n" + "=" * 70)
    
    # Сохранение результата в JSON
    output_file = Path(__file__).parent / "calculation_result.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"Результат сохранен в: {output_file}")

