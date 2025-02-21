import segno
import base64
from io import BytesIO

def generate_drug_qr(drug, drug_illnesses):
    """
    Формирует QR-код для объекта Drug.
    
    Параметры:
      drug – экземпляр модели Drug
      drug_illnesses – QuerySet или список объектов DrugIllness, связанных с drug
      
    Данные QR-кода содержат:
      - Название, описание и цену лекарства.
      - Список болезней, которые лечатся этим лекарством, с описанием клинических испытаний.
      - Дату завершения заявки (completed_at)
    """
    # Формируем начальную информацию
    info = f"Лекарство: {drug.name}\n"
    info += f"Описание: {drug.description or 'Нет описания'}\n"
    info += f"Цена: {drug.price}р.\n\n"
    info += "Болезни и клинические испытания:\n"
    
    if drug_illnesses:
        for di in drug_illnesses:
            # Здесь можно использовать di.illness.name и di.trial для испытаний
            info += f" - {di.illness.name}: испытания - {di.trial or 'нет данных'}\n"
    else:
        info += "Нет данных по болезням или испытаниям.\n"
    
    # Добавляем дату завершения, если она есть
    if drug.completed_at:
        completed_at_str = drug.completed_at.strftime('%Y-%m-%d %H:%M:%S')
        info += f"\nДата завершения заявки: {completed_at_str}"
    
    # Генерация QR-кода
    qr = segno.make(info)
    buffer = BytesIO()
    qr.save(buffer, kind='png')
    buffer.seek(0)
    
    # Конвертация изображения в base64
    qr_image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    
    return qr_image_base64
