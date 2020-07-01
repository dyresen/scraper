import requests
import re
import itertools
import argparse
from multiprocessing import Pool
from bs4 import BeautifulSoup

def url_valid(url="https://kolonial.no/"):
    #For aa sjekke om en side returnerer 404 eller ikke
    response = requests.get(url)
    if response.status_code == 404:
        return False
    else:
        return True

def get_content(url="https://kolonial.no/"):
    #Denne funksjonen mater beautiful soup
    try:
        page_content = requests.get(url).content
    except:
        print("oops, can not load page content")
    else:
        return page_content

def parse_content(html):
    soup = BeautifulSoup(html, 'html.parser')
    return soup

def find_all_categories(html):
    all_links = []
    #Her kan jeg finne alle kategoriene
    soup = BeautifulSoup(html, 'html.parser')
    for link in soup.find_all('a'):
        all_links.append(link.get('href'))

    #print(all_links)
    # As we can't iterate over None type objects, we'll filter the list here
    # before extracting all the categories
    all_links = filter(None, all_links)
    kategorier = [item for item in all_links if "kategorier" in item]
    #print(kategorier)
    #for i in all_links:
    #   print(i)
    #print(kategorier[1:])
    return kategorier[1:]

def get_sub_categories(category):
    sub_categories = []
    try:
        links = []
        #Takes on category as an argument
        url = f"https://kolonial.no{category}"
        html = get_content(url)
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a'):
            links.append(link.get('href'))

        links = filter(None, links)

        sub_categories = []
        #sub_categories = [item for item in links if "kategorier" in item]
        sub_cat = "{}".format(category)
        for cat in links:
            if sub_cat in cat:
                sub_categories.append(cat)
        sub_categories = sub_categories[2:]
    except:
        print("We couldn't get subcategories")
    return sub_categories


def get_products(sub_category):
    links = []
    products = []
    url = f"https://kolonial.no{sub_category}"
    #print(url)
    try:
        html = get_content(url)
        soup = BeautifulSoup(html, 'html.parser')
    
        for link in soup.find_all('a'):
            links.append(link.get('href'))
    
        links = filter(None, links)

        # products = [item for item in links if re.match("/produkter/\d", item) in item]
        for link in links:
            #print(link)
            if re.match("/produkter/\d", link):
                products.append(link) 
    except:
        pass
    #print(products)
    return products


def get_data(product):
    #print(product)
    try:
        url = f"https://kolonial.no{product}"
        html = get_content(url)
        soup = BeautifulSoup(html, 'html.parser')
        price = soup.find("meta", property="product:price:amount").get('content')
        product = soup.find("meta", property="og:title").get('content')
        print(product + ': ' + price)
    except:
        print("ooops, we couldn't print this product")




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Small script for scraping products and price from kolonial.no')
    parser.add_argument('-a', action='store', dest='aggro_level',
                    help='Sett an integer spesifying the amount of prosesses to use. The higher the number, the  more aggressive the crawler will be. Be nice! :) ')
    parser.add_argument('-c', action='store', dest='category',
                    help='Here you can specify a category, eg "26-kjott-og-kylling. If no category is spesified, we will try to crawl all categories and subcategories"')
    arguments = parser.parse_args()
    
    #print(arguments.category)

    if arguments.category == None:
        url_valid()
        page = get_content()
        parse_content(page)
    
        primary_categories = find_all_categories(page)
        #print(primary_categories)
    else:
        primary_categories = [] 
        primary_categories.append(f"/kategorier/{arguments.category}/")
        #print(primary_categories)
    
    tmp_list = []
    for primary_category in primary_categories:
        sub_categories = get_sub_categories(primary_category)
        tmp_list.append(sub_categories)
      
    chain_object = itertools.chain.from_iterable(tmp_list)
    flat_list = list(chain_object)

    #Get unique values from the flattened list by converting it to a set and back to a list
    tmp_set = set(flat_list)
    all_categories = list(tmp_set)
    print(all_categories)

    #Run trough all categories and fetch the products
    for cat in all_categories:
        products = get_products(cat)
        with Pool(int(arguments.aggro_level)) as p:
            p.map(get_data, products)
