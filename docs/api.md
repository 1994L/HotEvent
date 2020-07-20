# 说明
| 代码 | 返回msg | 详细描述 |
|:-------------:|:-------------|---|
| 0 | success | 请求成功 |
| 4001 | db error | 查询错误或者数据库崩溃 |
| 4101 | param error | 缺失参数或者参数错误 |
| 4201 | unknown error | 内部程序发生故障，原因不明 |
| 4301 | 自定义错误 | 错误信息随msg返回 |

# API
## 1. 航班查询
### API URL  
```
https://innovaapi.aminer.cn/covid/api/v1/flight?flynum=CA111&flydate=20200320
```
### HTTP Method
```
GET
```
### 输入参数  
| 名称             | 说明                      |必选|
| ----------------| ------------------------- |:--:|
| flynum          | 航班号，比如CA111           |是|
| flydate         | 查询日期，比如20200320      |是|  
### 输出结果  
```
{
    "code": 0,
    "msg": "success",
    "data": {
        "flyinfo": "中国国航 CA111",
        "dplan": "09:30",
        "origin": "北京首都T3",
        "aplan": "13:15",
        "destination": "香港T1",
        "status": "计划"
    }
}
```   
## 2. 疫情预测  
### API URL  
```
https://innovaapi.aminer.cn/covid/api/v1/pneumonia/prediction
```
### HTTP Method
```
GET
```
### 输入参数  
无
### 输出结果  
```
{
    "code": 0,
    "msg": "success",
    "data": {
        "overall": [
            {
                "date": "2020-03-19",
                "real": 0,
                "forcast": 81054,
                "curedCount": 0,
                "cureIncr": 0,
                "forcastCureIncr": 645,
                "forcastConfirmedIncr": 5
            },
            ...
        ],
        "nohubei": [
            {
                "date": "2020-03-17",
                "real": 0,
                "forcast": 13202,
                "forcastConfirmedIncr": 0,
                "cureIncr": 0,
                "forcastCureIncr": 39
            },
            ...
        ],
        "hubei": [
            {
                "date": "2020-03-19",
                "confirmedIncr": 0,
                "forcastConfirmedIncr": 5,
                "cureIncr": 0,
                "real": 0,
                "forcast": 67851,
                "forcastCureIncr": 887
            },
            ...
        ],
        "world": {
            "nochina": [
                {
                    "date": "2020-03-20",
                    "real": 2269,
                    "forcast": 8685
                },
                ...
            ],
            "Iran": [
                {
                    "date": "2020-03-20",
                    "real": 0,
                    "forcast": 16609
                },
                ...
            ],
            "Italy": [
                {
                    "date": "2020-03-20",
                    "real": 0,
                    "forcast": 22756
                },
                ...
            ],
            "Germany": [
                {
                    "date": "2020-03-20",
                    "real": 0,
                    "forcast": 3938
                },
                ...
            ],
            "France": [
                {
                    "date": "2020-03-21",
                    "real": 0,
                    "forcast": 5605
                },
                ...
            ]
        }
    }
}
```   
## 3. 疫情数据显示（全国，世界，流入）
### API URL  
```
https://innovaapi.aminer.cn/covid/api/v1/pneumonia/data
```
### HTTP Method
```
GET
```
### 输入参数  
| 名称             | 说明                      |必选|
| ----------------| ------------------------- |:--:|
| type          | 查询类型，0：全国，1：世界，2：流入|否，默认是0|
### 输出结果  
```
# type=0
{
    "code": 0,
    "msg": "success",
    "data": {
        "overall": {...
        },
        "area": [...
        ]
    }
}
# type=1
{
    "code": 0,
    "msg": "success",
    "data": [
        {各个国家的疫情数据信息},
        ...
    ]
}
# type=2
{
    "code": 0,
    "msg": "success",
    "data": [
        {
            "source": {
                "country": "意大利",
                "province": "",
                "city": "贝加莫",
                "pos": [
                    "45.696774",
                    "9.677389"
                ],
                "time": ""
            },
            "target": {
                "country": "中国",
                "province": "浙江省",
                "city": "青田县",
                "pos": [
                    "28.240873",
                    "120.147754"
                ],
                "time": "2020-02-28"
            },
            "confirmedTime": "2020-03-01",
            "gender": 0
        },
        ...
    ]
}
```   
## 4. 预测算法变更日志
### API URL  
```
https://innovaapi.aminer.cn/covid/api/v1/pneumonia/changelog
```
### HTTP Method
```
GET
```
### 输入参数  
无
### 输出结果  
```
{
    "code": 0,
    "msg": "success",
    "data": [
        {
            "time": "2020-03-12 13:00",
            "content": "根据世界卫生组织发布的全球疫情数据，预测世界疫情较为严重国家的疫情发展趋势。",
            "id": "5e69d6c0449a9e214c8e06e9"
        },
        ... 
    ]     
}        
```   
## 5. 航班风险预测
### API URL  
```
https://innovaapi.aminer.cn/covid/api/v1/pneumonia/flight-risk
```
### HTTP Method
```
GET
```
### 输入参数  
| 名称             | 说明                      |必选|
| ----------------| ------------------------- |:--:|
| flynum         | 航班号，例如：CA111|否，默认是None, 与area必须有一个有值|
| area         | 地区， 例如：洛杉矶|否，默认是None，与flynum必须有一个有值|
### 输出结果  
- 成功
     
flynum:   
```json
{
    "code": 0,
    "msg": "success",
    "data": {
        "depCity": "美国",
        "arrCity": "韩国",
        "forcast": 0.76
    }
}      
```  
area:   
```json
{
    "code": 0,
    "msg": "success",
    "data": {
        "forcast": 0.8
    }
}      
```
- 失败
```json
{
    "code": 4101,
    "msg": "param error",
    "data": null
}
```
## 6. 专家新闻抓取展示
### API URL  
```
https://innovaapi.aminer.cn/covid/api/v1/experts/news
```
### HTTP Method
```
POST
```
### 输入参数  
| 名称             | 说明                      |必选|
| ----------------| ------------------------- |:--:|
| ids              | 专家id列表                |是|
| kw              | 抓取新闻关键词， 例如：病毒|否，默认是None|
### 输出结果  
- 成功
     
flynum:   
```json
{
    "code": 0,
    "msg": "success",
    "data": [
        {
            "id": "5633ebca45cedb339acf818d",
            "news": [
                {
                    "title": "病毒下个冬天可能再次回来:别慌,一切都在向好的方向发展",
                    "source": "腾讯新闻",
                    "time": "2020年03月02日 01:23",
                    "desc": "关注我,用最朴实的语言带你了解高校,了解大学生活。“病毒猎手”利普金教授(Walter Ian Lipkin),在与杨澜的专访中说到:Y:您的意思是,当我们在武汉华南海鲜市场...",
                    "url": "https://new.qq.com/omn/20200302/20200302A00I7100.html"
                }
            ]
        }
    ]
}      
```  
## 7. 疫情数据集展示
### API URL  
```
https://innovaapi.aminer.cn/covid/api/v1/pneumonia/dataset
```
### HTTP Method
```
GET
```
### 输入参数  
| 名称             | 说明                      |必选|
| ----------------| ------------------------- |:--:|
| sortby              | 排序字段， 例如: Time|否，默认是Time|
| order              | 排序顺序{1: 正序, -1: 倒序}， 例如: 1|否，默认是1|
### 输出结果  
```json
{
    "code": 0,
    "msg": "success",
    "data": [
        {
            "Title_en": "Italy COVID-19 epidemic data",
            "Title_zh": "意大利COVID-19疫情数据",
            "Action": [
                "https://www.kaggle.com/sudalairajkumar/covid19-in-italy",
                "https://originalstatic.aminer.cn/misc/cokg19/Italy-COVID-epidemic-data.zip"
            ],
            "Description_en": "Admission statistics of patients with new coronary pneumonia in Italy",
            "Description_zh": "意大利新冠肺炎患者入院统计记录",
            "Category_en": [
                "pandemic"
            ],
            "Category_zh": [
                "疫情"
            ],
            "Provider_en": "kaggle",
            "Provider_zh": "kaggle",
            "Time": "2020.04.07",
            "Update_time": "2020.04.07",
            "id": "5e8d994be294332df892a368"
        }
    ]
}
```
## 8. 添加疫情数据集
### API URL  
```
https://innovaapi.aminer.cn/covid/api/v1/pneumonia/dataset
```
### HTTP Method
```
POST
```
### 输入参数  
```json
{
    "data": {
        "Title_en": "Italy COVID-19 epidemic data123",
        "Title_zh": "意大利COVID-19疫情数据123",
        "Action": [
            "https://www.kaggle.com/sudalairajkumar/covid19-in-italy",
            "https://originalstatic.aminer.cn/misc/cokg19/Italy-COVID-epidemic-data.zip"
        ],
        "Description_en": "Admission statistics of patients with new coronary pneumonia in Italy",
        "Description_zh": "意大利新冠肺炎患者入院统计记录",
        "Category_en": [
            "pandemic"
        ],
        "Category_zh": [
            "疫情"
        ],
        "Provider_en": "kaggle",
        "Provider_zh": "kaggle"
    }
}
```
### 输出结果  
```json
{
    "code": 0,
    "msg": "success",
    "data": {
            "Title_en": "Italy COVID-19 epidemic data123",
            "Title_zh": "意大利COVID-19疫情数据123",
            "Action": [
                "https://www.kaggle.com/sudalairajkumar/covid19-in-italy",
                "https://originalstatic.aminer.cn/misc/cokg19/Italy-COVID-epidemic-data.zip"
            ],
            "Description_en": "Admission statistics of patients with new coronary pneumonia in Italy",
            "Description_zh": "意大利新冠肺炎患者入院统计记录",
            "Category_en": [
                "pandemic"
            ],
            "Category_zh": [
                "疫情"
            ],
            "Provider_en": "kaggle",
            "Provider_zh": "kaggle",
            "Time": "2020.04.07",
            "Update_time": "2020.04.07",
            "id": "5e8d994be294332df892a368"
    }
}
```
## 9. 修改疫情数据集
### API URL  
```
https://innovaapi.aminer.cn/covid/api/v1/pneumonia/dataset/<string: id>
```
### HTTP Method
```
PUT
```
### 输入参数  
```json
{
    "data": {
        "Title_en": "Italy COVID-19 epidemic data123",
        "Title_zh": "意大利COVID-19疫情数据123",
        "Action": [
            "https://www.kaggle.com/sudalairajkumar/covid19-in-italy",
            "https://originalstatic.aminer.cn/misc/cokg19/Italy-COVID-epidemic-data.zip"
        ],
        "Description_en": "Admission statistics of patients with new coronary pneumonia in Italy",
        "Description_zh": "意大利新冠肺炎患者入院统计记录",
        "Category_en": [
            "pandemic"
        ],
        "Category_zh": [
            "疫情"
        ],
        "Provider_en": "kaggle",
        "Provider_zh": "kaggle"
    }
}
```
### 输出结果  
```json
{
    "code": 0,
    "msg": "success",
    "data": {
            "Title_en": "Italy COVID-19 epidemic data123",
            "Title_zh": "意大利COVID-19疫情数据123",
            "Action": [
                "https://www.kaggle.com/sudalairajkumar/covid19-in-italy",
                "https://originalstatic.aminer.cn/misc/cokg19/Italy-COVID-epidemic-data.zip"
            ],
            "Description_en": "Admission statistics of patients with new coronary pneumonia in Italy",
            "Description_zh": "意大利新冠肺炎患者入院统计记录",
            "Category_en": [
                "pandemic"
            ],
            "Category_zh": [
                "疫情"
            ],
            "Provider_en": "kaggle",
            "Provider_zh": "kaggle",
            "Time": "2020.04.07",
            "Update_time": "2020.04.07",
            "id": "5e8d994be294332df892a368"
    }
}
```
## 9. 删除疫情数据集
### API URL  
```
https://innovaapi.aminer.cn/covid/api/v1/pneumonia/dataset/<string: id>
```
### HTTP Method
```
DELETE
```
### 输入参数  
```
https://innovaapi.aminer.cn/covid/api/v1/pneumonia/dataset/5e8d994be294332df892a368
```
### 输出结果  
```json
{
    "code": 0,
    "msg": "success",
    "data": []
}
```
## 10. 展示反馈数据
### API URL  
```
https://innovaapi.aminer.cn/covid/api/v1/feedback
```
### HTTP Method
```
GET
```
### 输入参数  
| 名称             | 说明                      |必选|
| ----------------| ------------------------- |:--:|
| cla              | 反馈类别                |否，默认是Covid19_Datasets_dingYue|
| sortby              | 排序字段， 例如: date|否，默认是date|
| order              | 排序顺序{1: 正序, -1: 倒序}， 例如: 1|否，默认是-1|
### 输出结果  
```json
{
    "code": 0,
    "msg": "success",
    "data": [
        {
            "ip": "111.196.64.137",
            "pid": "https://covid-19.aminer.cn/datasets",
            "comment": "https://www.aminer.cn/data-covid19/",
            "cla": "Covid19_Datasets__feedBack",
            "degree": "2042199365@qq.com",
            "positive": "",
            "negtive": "",
            "date": "2020-04-08 10:44:43",
            "id": "5e8d3a9c9e4f2d85c735d071"
        }
    ]
}
```
## 11. 修改反馈数据状态
### API URL  
```
https://innovaapi.aminer.cn/covid/api/v1/feedback/<string: id>
```
### HTTP Method
```
PUT
```
### 输入参数  
| 名称             | 说明                      |必选|
| ----------------| ------------------------- |:--:|
| option              | 修改操作 0: 确认,1: 删除,2: 取消确认,3: 取消删除         |否，默认是0|
### 输出结果  
```json
{
    "code": 0,
    "msg": "success",
    "data": []
}
```
## 12. 新型肺炎实体链接分析
### API URL  
```
https://innovaapi.aminer.cn/covid/api/v1/pneumonia/entitylink
```
### HTTP Method
```
GET
```
### 输入参数  
| 名称             | 说明                      |必选|
| ----------------| ------------------------- |:--:|
| news              |新闻文本           |是|
### 输出结果  
```json
{
    "code": 0,
    "msg": "success",
    "data": [
        {
            "label": "positive",
            "url": "https://covid-19.aminer.cn/kg/resource/R3842",
            "abstractInfo": {
                "enwiki": null,
                "baidu": null,
                "zhwiki": null,
                "COVID": {
                    "properties": {},
                    "relations": [
                        {
                            "relation": "belongTo",
                            "url": "https://covid-19.aminer.cn/kg/class/drug",
                            "label": "drug",
                            "forward": "True"
                        }
                    ]
                }
            },
            "pos": [
                {
                    "start": 14,
                    "end": 22
                }
            ]
        },
        {
            "label": "Department",
            "url": "https://covid-19.aminer.cn/kg/class/department",
            "abstractInfo": {
                "enwiki": null,
                "baidu": null,
                "zhwiki": null,
                "COVID": {
                    "properties": {},
                    "relations": [
                        {
                            "relation": "subClassOf",
                            "url": "https://covid-19.aminer.cn/kg/class/organization",
                            "label": "organization",
                            "forward": "True"
                        },
                        {
                            "relation": "belongTo",
                            "url": "https://covid-19.aminer.cn/kg/resource/R259",
                            "label": "internal medicine",
                            "forward": "False"
                        }
                    ]
                }
            },
            "pos": [
                {
                    "start": 131,
                    "end": 141
                }
            ]
        }
    ]
}
```
## 13. 新型肺炎url查询
### API URL  
```
https://innovaapi.aminer.cn/covid/api/v1/pneumonia/entity
```
### HTTP Method
```
GET
```
### 输入参数  
| 名称             | 说明                      |必选|
| ----------------| ------------------------- |:--:|
| url              |实体URL           |是|
| lang          |选择中英文    zh/en      |是|
### 输出结果  
```json
{
    "code": 0,
    "msg": "success",
    "data": {
        "label": "中毒性高铁血红蛋白血",
        "url": "https://covid-19.aminer.cn/kg/resource/R10657",
        "abstractInfo": {
            "enwiki": null,
            "baidu": null,
            "zhwiki": null,
            "COVID": {
                "properties": {
                    "发病部位": "全身",
                    "临床表现": "头痛疲劳紫绀发绀"
                },
                "relations": [
                    {
                        "relation": "属于",
                        "url": "https://covid-19.aminer.cn/kg/class/disease",
                        "label": "疾病",
                        "forward": "True"
                    }
                ]
            }
        },
        "hot":0.0
    }
}
```
## 14. 新型肺炎实体查询
### API URL  
```
https://innovaapi.aminer.cn/covid/api/v1/pneumonia/entityquery
```
### HTTP Method
```
GET
```
### 输入参数  
| 名称             | 说明                      |必选|
| ----------------| ------------------------- |:--:|
| entity              |实体名称(zh/en)           |是|
| mini                |实体查询/中英文对照(0/1)        ｜默认值为0|
### 输出结果  
```json
{
    "code": 0,
    "msg": "success",
    "data": [
        {
            "label": "新冠病毒",
            "url": "https://covid-19.aminer.cn/kg/resource/R25833",
            "abstractInfo": {
                "enwiki": null,
                "baidu": null,
                "zhwiki": null,
                "COVID": {
                    "properties": {
                        "潜伏期": "1-14天，多为3-7天",
                        "鉴别诊断": "主要与流感病毒、副流感病毒、腺病毒、呼吸道合胞病毒、鼻病毒、人偏肺病毒、SARS冠状病毒等其他已知病毒性肺炎鉴别，与肺炎支原体、衣原体肺炎及细菌性肺炎等鉴别。此外，还要与非感染性疾病，如血管炎、皮肌炎和机化性肺炎等鉴别。",
                        "实验室检查": "发病早期外周血白细胞总数正常，淋巴细胞计数减少，部分患者可出现肝酶、乳酸脱氢酶（LDH）、肌酶和肌红蛋白增高；部分危重者可见肌钙蛋白增高。多数患者C反应蛋白（CRP）和血沉升高，降钙素原正常。严重者D-二聚体升高、外周血淋巴细胞进行性减少。 在鼻咽拭子、痰、下呼吸道分泌物、血液、粪便等标本中可检测出新型冠状病毒核酸。",
                        "基本传染指数": "2.2",
                        "胸部影像学": "早期呈现多发小斑片影及间质改变，以肺外带明显。进而发展为双肺多发磨玻璃影、浸润影、严重者可出现肺实变，胸腔积液少见。",
                        "生理机能": "体外分离培养时，2019-nCoV 96个小时左右即可在人呼吸道上皮细胞内发现，而在Vero E6 和Huh-7细胞系中分离培养需约6天。病毒对紫外线和热敏感，56℃ 30分钟、乙醚、75%乙醇、含氯消毒剂、过氧乙酸和氯仿等脂溶剂均可有效灭活病毒，氯已定不能有效灭火病毒。",
                        "死亡率": "14",
                        "基因特征": "其基因特征与SARSr-CoV和MERSr-CoV有明显区别。目前研究显示与蝙蝠SARS样冠状病毒（bat-SL-CoVZC45）同源性达85%以上。",
                        "结构": "有包膜，颗粒呈圆形或者椭圆形，常为多形性，直径60-140nm。"
                    },
                    "relations": [
                        {
                            "relation": "疑似宿主",
                            "url": "https://covid-19.aminer.cn/kg/resource/R250",
                            "label": "中华菊头蝠",
                            "forward": "True"
                        },
                        {
                            "relation": "导致",
                            "url": "https://covid-19.aminer.cn/kg/resource/R332",
                            "label": "新型冠状病毒肺炎",
                            "forward": "True"
                        }
                    ]
                }
            }
        }
    ]
}
```

## 15. 实体热度更新
### API URL  
```
https://innovaapi.aminer.cn/covid/api/v1/pneumonia/view
```
### HTTP Method
```
GET
```
### 输入参数 
| 名称             | 说明                      |必选|
| ----------------| ------------------------- |:--:|
| url              |实体命名空间           |是|

## 16. 实体联想词
### API URL  
```
https://innovaapi.aminer.cn/covid/api/v1/pneumonia/hit
```
### HTTP Method
```
GET
```
### 输入参数 
| 名称             | 说明                      |必选|
| ----------------| ------------------------- |:--:|
| name              |用户输入（中文/英文/拼音）           |是|
### 输出结果 
```json
{
    "code": 0,
    "msg": "success",
    "data": [
        {
            "url": "https://covid-19.aminer.cn/kg/resource/R7541",
            "label_zh": "并发症白内障",
            "label_en": "complications cataract",
            "lang": "zh",
            "hot": 0.0
        },
        {
            "url": "https://covid-19.aminer.cn/kg/resource/R8122",
            "label_zh": "并殖吸虫病",
            "label_en": "paragonimiasis",
            "lang": "zh",
            "hot": 0.0
        },
        {
            "url": "https://covid-19.aminer.cn/kg/class/virus",
            "label_zh": "病毒",
            "label_en": "virus",
            "lang": "zh",
            "hot": 0.8000736575631411
        }
    ]
}
```
## 17. KBQA
### API URL  
```
https://innovaapi.aminer.cn/covid/api/v1/pneumonia/qa_answer
```
### HTTP Method
```
GET
```
### 输入参数 
| 名称             | 说明                      |必选|
| ----------------| ------------------------- |:--:|
| entity              |实体名称           |是|
| relation              |关系名称           |是|
### 输出结果
```json
{
    "code": 0,
    "msg": "success",
    "data": [
        {"entity_name":"β属的新型冠状病毒",
        "entity_url":"https://covid-19.aminer.cn/kg/resource/R25840"},
        {"entity_name":"病毒",
        "entity_url":"https://covid-19.aminer.cn/kg/class/virus"}
    ]
}
```
对于查询到没有链接的实体，其entity_url的值为空

## 18. Fusion QA
### API URL  
```
https://innovaapi.aminer.cn/covid/api/v1/pneumonia/QA
```
### HTTP Method
```
GET
```
### 输入参数 
| 名称             | 说明                      |必选|
| ----------------| ------------------------- |:--:|
| question              |问句           |是|
### 输出结果
```json
{
    "code": 0,
    "msg": "success",
    "data": [
        {
            "answers": [
                {
                    "answer": "目前认为，传染源主要是 SARS-CoV-2 感染的患者。无症状或症状轻微的隐性感染 者也可能成为传染源。目前的研究证据提示处于潜伏期的患者可能存在一定的传染性，在恢复期早期的患者可以检测到病毒的存在，也可能具有一定的传染性。",
                    "match_question": "新型冠状病毒肺炎的传染源是什么？",
                    "score": 0.8660254037844388,
                    "source": "es"
                },
                {
                    "answer": "新型冠状病毒-->传染源： 无症状感染者。了解更多详情，可点击<a href=\"https://covid-19.aminer.cn/kg/resource/R25844\" target=\"_blank\">无症状感染者</a> ",
                    "match_question": "新型冠状病毒-->传染源 ？",
                    "score": null,
                    "source": "kg"
                }
            ],
            "question": "新型冠状病毒的传染源"
        }
    ]
}
```
## 19. 实时更新展示
### API URL  
```
https://innovaapi.aminer.cn/covid/api/v1/pneumonia/show_update
```
### HTTP Method
```
GET
```
### 输出结果
```json
{
    "code": 0,
    "msg": "success",
    "data": [
        {
            "title": "Complications and outcomes of SARS-CoV-2 in pregnancy: where and what is the evidence?",
            "entities": [
                {
                    "url": "https://covid-19.aminer.cn/kg/resource/patient",
                    "label_zh": "病人",
                    "label_en": "patient"
                }
            ],
            "ObjectId": "5f0580d996415b7fce71c05b",
            "source": "paper"
        },
        {
            "title": "Hunting severe acute respiratory syndrome coronavirus 2 (2019 novel coronavirus): From laboratory testing back to basic research.",
            "entities": [
                {
                    "url": "https://covid-19.aminer.cn/kg/resource/real-time_reverse_transcription_polymerase_chain_reaction",
                    "label_zh": "实时逆转录聚合酶链反应",
                    "label_en": "real-time reverse transcription polymerase chain reaction"
                },
                {
                    "url": "https://covid-19.aminer.cn/kg/resource/quantitative_polymerase_chain_reaction",
                    "label_zh": "定量聚合酶链反应",
                    "label_en": "quantitative polymerase chain reaction"
                }
            ],
            "ObjectId": "5f0580d996415b7fce71c05c",
            "source": "paper"
        }
    ]
}
```