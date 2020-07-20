from datetime import datetime
from bson import ObjectId

from apps.mongo_client import CovidDatasetDB, FeedbackDB


cov_dataset_col = CovidDatasetDB()
fb_col = FeedbackDB()


def query_all_dataset(sortby: str, order: int):
    dataset_cursor = cov_dataset_col.find_many({'is_delete': {'$ne': True}}).sort(sortby, order)
    datasets = []
    count = 0
    tobe_inserted = {}
    for dataset in dataset_cursor:
        dataset['id'] = str(dataset.pop('_id'))
        if 'position' in dataset and dataset['position']['key'] == sortby:
            if dataset['position']['value'] > count:
                tobe_inserted[dataset['position']['value']] = dataset
                continue
            else:
                datasets.insert(dataset['position']['value'], dataset)
        else:
            datasets.append(dataset)
        count += 1
    for k, v in tobe_inserted.items():
        datasets.insert(k, v)

    # for dataset in dataset_cursor:
    #     dataset['id'] = str(dataset.pop('_id'))
    #     datasets.append(dataset)
    return datasets


def add_dataset(dataset: dict):
    now = datetime.now()
    dataset['Time'] = now.strftime('%Y.%m.%d')
    dataset['Update_time'] = now.strftime('%Y-%m-%d %H:%M:%S')
    cov_dataset_col.insert_one(dataset)
    dataset['id'] = str(dataset.pop('_id'))
    return dataset


def del_dataset_by_id(id: str):
    cov_dataset_col.update_one({'_id': ObjectId(id)}, {'$set': {'is_delete': True}})


def edit_dataset_by_id(id: str, data: dict):
    dataset_col = cov_dataset_col.find_one({'_id': ObjectId(id)})
    if dataset_col:
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        update_data = {}
        for k, v in data.items():
            if k in dataset_col:
                update_data[k] = v
        update_data['Update_time'] = now_str
        cov_dataset_col.update_one({'_id': ObjectId(id)}, {'$set': update_data})
        ret = cov_dataset_col.find_one({'_id': ObjectId(id)})
        ret['id'] = str(ret.pop('_id'))
        return ret
    return {}


def query_feedback(cla: str, sortby: str, order: int):
    feebback_cursor = fb_col.find_many({'cla': cla}).sort(sortby, order)
    ret = []
    for fb in feebback_cursor:
        fb['id'] = str(fb.pop('_id'))
        fb['comment'] = fb['comment'].replace('\n', ' ')
        ret.append(fb)
    return ret


def edit_feedback(id: str, option: int):
    '''
    {
        0: 确认,
        1: 删除,
        2: 取消确认,
        3: 取消删除
    }
    :param id:
    :return:
    '''
    if option == 0:
        fb_col.update_one({'_id': ObjectId(id)}, {'$set': {'is_confirm': True}})
    elif option == 1:
        fb_col.update_one({'_id': ObjectId(id)}, {'$set': {'is_delete': True}})
    elif option == 2:
        fb_col.update_one({'_id': ObjectId(id)}, {'$set': {'is_confirm': False}})
    else:
        fb_col.update_one({'_id': ObjectId(id)}, {'$set': {'is_delete': False}})


if __name__ == '__main__':
    dataset_cursor = [
        {'name': 1},
        {'name': 2},
        {'name': 3, 'position': 6},
        {'name': 4},
        {'name': 5, 'position': 1},
        {'name': 6},
        {'name': 7, 'position': 2},
        {'name': 8}
    ]

    datasets = []
    count = 0
    tobe_inserted = {}
    for dataset in dataset_cursor:
        if 'position' in dataset and dataset['position'] > count:
            tobe_inserted[dataset['position']] = dataset
            continue
        elif 'position' in dataset and dataset['position'] < count:
            datasets.insert(dataset['position'], dataset)
        else:
            datasets.append(dataset)
        count += 1
    for k, v in tobe_inserted.items():
        datasets.insert(k, v)

    for i in datasets:
        print(i)