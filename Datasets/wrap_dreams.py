import csv

def wrap_dreams_to_xml(csv_path, output_path):
    """
    将DB.csv中的梦境数据包装成XML格式

    输入格式: Series, Dream_Text, Word_Count
    输出格式: <dream id="alta_1"> [Dream text content here] </dream>
    """
    series_counter = {}

    with open(csv_path, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        with open(output_path, 'w', encoding='utf-8') as outfile:
            for row in reader:
                series = row['Series']
                series_counter[series] = series_counter.get(series, 0) + 1
                dream_id = f"{series}_{series_counter[series]}"
                dream_text = row['Dream_Text']
                outfile.write(f'<dream id="{dream_id}"> {dream_text} </dream>\n')

if __name__ == '__main__':
    wrap_dreams_to_xml('DB.csv', 'DB_wrapped.xml')
    print("数据已包装完成，输出文件: DB_wrapped.xml")