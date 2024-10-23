from django.shortcuts import render
from test_data import ILLNESS, DRUG  # предполагаем, что данные перенесены в файл 


def index(request):
    illness_name = request.GET.get('illness')
    selected_illness = DRUG[0]
    count = len(DRUG[0]['illnesses'])
    if illness_name:
        illnesses=[]
        for illness in ILLNESS:
            if illness_name.lower() in illness['name'].lower():
                illnesses.append(illness)
        return render(request, 'index.html', {
            "illnesses": illnesses,
            'query': illness_name,
            "drug": 1,
            'count': count,
            })
    
    else:
        return render(request, 'index.html', {"illnesses": ILLNESS, "drug": 1, 'count': count})

def illness(request, illness_id):
    for ill in ILLNESS:
        if ill['id'] == illness_id:
            illness = ill
            break
    return render(request, 'illness.html', {"illness": illness})
    
    # Если болезнь не найдена
    return render(request, '404.html', {"error": "Illness not found"})

def drug(request, drug_id):
    curr_drug = next((drug for drug in DRUG if drug['id'] == drug_id), None)
    if not curr_drug:
        return render(request, 'drug.html')

    return render(request, 'drug.html', {
        "drug": curr_drug,
        "drugs_with_names": drugs_with_names,
        "total_person_price": total_person_price,
        "total": total,
        "count_dishes": total_dish_count
    })

def get_illness_by_id(illness_id):
    illness = next((illness for illness in ILLNESS if illness['id'] == illness_id), None)
    if illness is None:
        raise ValueError(f"Illness with ID {illness_id} not found.")
    return illness

def get_illnesses_by_ids(illness_ids):
    # Returns illnesses that match the provided IDs
    return [illness for illness in ILLNESS if illness['id'] in illness_ids]

def drug(request, drug_id):
    drug_data = next((drug for drug in DRUG if drug['id'] == drug_id), None)
    
    if drug_data:
        # Correcting the access to illness 'Id' values
        illness_ids = [illness['Id'] for illness in drug_data['illnesses']]
        illness_result = [illness['сlinical_trial'] for illness in drug_data['illnesses']]
        ask_illnesses = get_illnesses_by_ids(illness_ids)
        illnesses_zip = zip(ask_illnesses, illness_result)

        context = {
            'ask_name': drug_data['name'],
            'illnesses_with_results': illnesses_zip,
            'ask_description': drug_data['description'],
        }

        return render(request, 'drug.html', context)
