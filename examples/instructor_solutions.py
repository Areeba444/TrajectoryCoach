"""Instructor answer key. Do not expose during no-AI transfer assessments."""
def qualifying_sales(values,threshold):
    return sum(v for v in values if v>=threshold)

def safe_average(values):
    return sum(values)/len(values) if values else None

def within_window(values,low,high):
    return [v for v in values if low<=v<=high]

def category_counts(categories):
    result={}
    for category in categories:result[category]=result.get(category,0)+1
    return result

def approved_minutes(records,minimum):
    return sum(minutes for minutes,approved in records if approved and minutes>=minimum)

def first_qualifying(values,threshold):
    return next((i for i,v in enumerate(values) if v>=threshold),None)
