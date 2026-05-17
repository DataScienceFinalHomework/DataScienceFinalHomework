### DB系列：全部来自DreamBank爬虫

DB：包括Series、Dream_Text和Word_Count。Series标注这是哪个梦境集，比方说Series同为"alta"的梦境，皆来自alta梦境集

DB_VADER：即用VADER工具处理过的DB，在原有列的基础上增加了pos、neg、neu和compound（VADER的功能就是读取Dream_Text并算出这四个值）；除此以外，我额外添加了difference，计算公式为(pos - neg)；以及log，计算公式为log((pos + 1e-5)/(neg + 1e-5))

DB_EMPATH：即用EMPATH工具处理过的DB，在原有列的基础上增加了194个EMPATH自带的预训练词汇类别。注意它们已经是被标准化了的，因此值域为[0,1]。以及显然不是每个梦都与194个主题都相关的，所以这是个稀疏矩阵。194个EMPATH自带的预训练词汇类别见下：

help,office,dance,money,wedding,domestic_work,sleep,medical_emergency,cold,hate,cheerfulness,aggression,occupation,envy,anticipation,family,vacation,crime,attractive,masculine,prison,health,pride,dispute,nervousness,government,weakness,horror,swearing_terms,leisure,suffering,royalty,wealthy,tourism,furniture,school,magic,beach,journalism,morning,banking,social_media,exercise,night,kill,blue_collar_job,art,ridicule,play,computer,college,optimism,stealing,real_estate,home,divine,sexual,fear,irritability,superhero,business,driving,pet,childish,cooking,exasperation,religion,hipster,internet,surprise,reading,worship,leader,independence,movement,body,noise,eating,medieval,zest,confusion,water,sports,death,healing,legend,heroic,celebration,restaurant,violence,programming,dominant_heirarchical,military,neglect,swimming,exotic,love,hiking,communication,hearing,order,sympathy,hygiene,weather,anonymity,trust,ancient,deception,fabric,air_travel,fight,dominant_personality,music,vehicle,politeness,toy,farming,meeting,war,speaking,listen,urban,shopping,disgust,fire,tool,phone,gain,sound,injury,sailing,rage,science,work,appearance,valuable,warmth,youth,sadness,fun,emotional,joy,affection,traveling,fashion,ugliness,lust,shame,torment,economics,anger,politics,ship,clothing,car,strength,technology,breaking,shape_and_size,power,white_collar_job,animal,party,terrorism,smell,disappointment,poor,plant,pain,beauty,timidity,philosophy,negotiate,negative_emotion,cleaning,messaging,competing,law,friends,payment,achievement,alcohol,liquid,feminine,weapon,children,monster,ocean,giving,contentment,writing,rural,positive_emotion,musical

DB_SPACY：即用SPACY工具处理过的DB，在原有列的基础上增加了person_list,location_list,noun_chunks,action_verbs,adjectives,sentence_count（都是SPACY自己算的）

### SDDB系列：全部来自Sleep and Dream DataBase下载

SDDB：包括Survey Name、Dream Text和Word Count。Survey Name标注这是哪个梦境集，比方说Survey Name同为"melvin-dreams"的梦境，皆来自melvin-dreams梦境集

SDDB_VADER：同DB_VADER

SDDB_EMPATH：同DB_EMPATH

SDDB_SPACY：同DB_SPACY

### entity_analysis_results

目前课题二已经处理的DB数据集5k条左右数据，包含实体出现的频率(已经降序排列)，以及对rank和freq的log值的简单处理
