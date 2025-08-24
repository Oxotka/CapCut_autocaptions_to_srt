#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для преобразования файла draft_info.json в файл субтитров captions-2.srt
"""

import json
import pyperclip


def create_ai_prompt(srt_content: str) -> str:
    """
    Создает промпт для нейросети на основе содержимого SRT файла
    
    Args:
        srt_content: содержимое SRT файла
        
    Returns:
        готовый промпт для нейросети
    """
    base_prompt = """Нужно перевести субтитры на английский язык 
1 Сохранять точное количество строк и оригинальные временные метки 
2 Использовать инструктивный, разговорный стиль с естественными английскими конструкциями 
3 Строго придерживаться терминологии

В итоге должен получиться текст в таком же формате как и был

"""
    
    return base_prompt + srt_content


def parse_time_microseconds(time_microseconds: int) -> str:
    """
    Преобразует время в микросекундах в формат SRT (HH:MM:SS,mmm)
    
    Args:
        time_microseconds: время в микросекундах
        
    Returns:
        строка времени в формате SRT
    """
    # Конвертируем микросекунды в секунды
    time_seconds = time_microseconds / 1000000
    
    # Вычисляем часы, минуты, секунды и миллисекунды
    hours = int(time_seconds // 3600)
    minutes = int((time_seconds % 3600) // 60)
    seconds = int(time_seconds % 60)
    milliseconds = int((time_seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def extract_subtitle_text(subtitle_cache_info: str) -> str:
    """
    Извлекает текст субтитров из поля subtitle_cache_info
    
    Args:
        subtitle_cache_info: JSON строка с информацией о субтитрах
        
    Returns:
        текст субтитров или пустая строка
    """
    if not subtitle_cache_info or subtitle_cache_info == "":
        return ""
    
    try:
        # Парсим JSON строку
        cache_data = json.loads(subtitle_cache_info)
        
        # Извлекаем текст из sentence_list
        if "sentence_list" in cache_data and cache_data["sentence_list"]:
            sentences = []
            for sentence in cache_data["sentence_list"]:
                if "text" in sentence:
                    sentences.append(sentence["text"])
            
            return " ".join(sentences)
        
        return ""
    except (json.JSONDecodeError, KeyError, TypeError):
        return ""


def convert_draft_info_to_srt(input_file: str, output_file: str) -> tuple[int, str]:
    """
    Конвертирует файл draft_info.json в формат SRT
    
    Args:
        input_file: путь к входному файлу draft_info.json
        output_file: путь к выходному файлу captions-2.srt
        
    Returns:
        кортеж (количество найденных субтитров, содержимое SRT файла)
    """
    try:
        # Читаем JSON файл
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Ищем поле subtitle_fragment_info_list
        subtitle_fragments = None
        
        # Рекурсивно ищем поле subtitle_fragment_info_list
        def find_subtitle_fragments(obj):
            if isinstance(obj, dict):
                if "subtitle_fragment_info_list" in obj:
                    return obj["subtitle_fragment_info_list"]
                for value in obj.values():
                    result = find_subtitle_fragments(value)
                    if result is not None:
                        return result
            elif isinstance(obj, list):
                for item in obj:
                    result = find_subtitle_fragments(item)
                    if result is not None:
                        return result
            return None
        
        subtitle_fragments = find_subtitle_fragments(data)
        
        if not subtitle_fragments:
            print("Ошибка: поле subtitle_fragment_info_list не найдено")
            return 0, ""
        
        # Фильтруем фрагменты с субтитрами
        subtitles_with_text = []
        for fragment in subtitle_fragments:
            if "subtitle_cache_info" in fragment and fragment["subtitle_cache_info"]:
                text = extract_subtitle_text(fragment["subtitle_cache_info"])
                if text.strip():
                    subtitles_with_text.append({
                        "start_time": fragment["start_time"],
                        "end_time": fragment["end_time"],
                        "text": text
                    })
        
        # Сортируем по времени начала
        subtitles_with_text.sort(key=lambda x: x["start_time"])
        
        # Формируем содержимое SRT файла
        srt_content = ""
        for i, subtitle in enumerate(subtitles_with_text, 1):
            start_time = parse_time_microseconds(subtitle["start_time"])
            end_time = parse_time_microseconds(subtitle["end_time"])
            text = subtitle["text"]
            
            srt_content += f"{i}\n"
            srt_content += f"{start_time} --> {end_time}\n"
            srt_content += f"{text}\n\n"
        
        # Записываем в SRT файл
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        print(f"Успешно создан файл {output_file}")
        print(f"Найдено {len(subtitles_with_text)} субтитров")
        
        return len(subtitles_with_text), srt_content
        
    except FileNotFoundError:
        print(f"Ошибка: файл {input_file} не найден")
        return 0, ""
    except json.JSONDecodeError as e:
        print(f"Ошибка парсинга JSON: {e}")
        return 0, ""
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return 0, ""


def main():
    """Основная функция"""
    # Путь к исходному файлу draft_info.json
    capcut_dir = "/Users/nikitaaripov/Movies/CapCut/User Data/Projects/com.lveditor.draft/"
    project_name = "0824"
    input_file = f"{capcut_dir}{project_name}/draft_info.json"
    
    # Создаем папку result если её нет
    import os
    result_dir = "result"
    os.makedirs(result_dir, exist_ok=True)
    
    # Формируем имя выходного файла с временной меткой
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(result_dir, f"captions_{timestamp}.srt")
    
    print(f"Конвертируем {input_file} в {output_file}...")
    
    subtitle_count, srt_content = convert_draft_info_to_srt(input_file, output_file)
    
    if subtitle_count > 0:
        print("Конвертация завершена успешно!")
        print(f"Результат сохранен в файл {output_file}")
        print(f"Файл находится в папке: {os.path.abspath(result_dir)}")
        
        # Создаем промпт для нейросети и копируем в буфер обмена
        ai_prompt = create_ai_prompt(srt_content)
        try:
            pyperclip.copy(ai_prompt)
            print("Промпт для нейросети скопирован в буфер обмена!")
            print("Теперь вы можете вставить его в любой AI-сервис для перевода субтитров.")
        except Exception as e:
            print(f"Ошибка при копировании в буфер обмена: {e}")
            print("Промпт для нейросети:")
            print("-" * 50)
            print(ai_prompt)
            print("-" * 50)
    else:
        print("Конвертация не удалась.")


if __name__ == "__main__":
    main()
