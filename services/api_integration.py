import requests
from storage.storage import save_country_to_csv
from logger.logger import log_info, log_error

def get_country_info(name_or_region):

    url_country = f"https://restcountries.com/v3.1/name/{name_or_region}?fullText=true"
    url_region = f"https://restcountries.com/v3.1/region/{name_or_region}"

    try:
      
        response_country = requests.get(url_country)
        if response_country.status_code == 200:
            country_data = response_country.json()[0]
            formatted = format_country_data(country_data)
            country_name = formatted["name"]
            formatted["famous_places"] = get_famous_places(country_name)

            save_country_to_csv(formatted)
            log_info(f"Fetched data for {formatted['name']}")
            return formatted

       
        response_region = requests.get(url_region)
        if response_region.status_code == 200:
            region_data = response_region.json()
            result = []
            for country in region_data:
                formatted = format_country_data(country)
                result.append(formatted)
            return result

        return None

    except Exception as e:
        return {"error": str(e)}


def format_country_data(data):
  
    name = data.get("name", {}).get("common", "N/A")
    
    official_name = data.get("name", {}).get("official", "N/A")
    
    capital = data.get("capital", ["N/A"])[0]
    
    population = data.get("population", "N/A")
    
    region = data.get("region", "N/A")
    
    subregion = data.get("subregion", "N/A")
    
    languages = ", ".join(data.get("languages", {}).values()) if data.get("languages") else "N/A"
    
    borders = ", ".join(data.get("borders", [])) if data.get("borders") else "None"
    
    timezones = ", ".join(data.get("timezones", [])) if data.get("timezones") else "N/A"
    
    flag = data.get("flags", {}).get("png", "")
    
    map = data.get("maps", {}).get("googleMaps", "#")
    
    currencies = ", ".join(
        [f"{v.get('name')} ({v.get('symbol')})" for v in data.get("currencies", {}).values()]
    ) if data.get("currencies") else "N/A"

    return {
        "name": name,
        "official_name": official_name,
        "capital": capital,
        "population": population,
        "region": region,
        "subregion": subregion,
        "languages": languages,
        "borders": borders,
        "timezones": timezones,
        "flag": flag,
        "map": map,
        "currencies": currencies
    }


def get_famous_places(country_name, limit=3):
  
    try:

        search_query = f"Tourist attractions in {country_name}"
        search_url = "https://en.wikipedia.org/w/api.php"

        search_params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": search_query,
            "utf8": 1
        }

        response = requests.get(search_url, params=search_params)
        data = response.json()

        famous_places = []
        if "query" in data and "search" in data["query"]:
            for i, place in enumerate(data["query"]["search"][:limit]):
                title = place["title"]

       
                details_url = "https://en.wikipedia.org/w/api.php"
                details_params = {
                    "action": "query",
                    "format": "json",
                    "prop": "extracts|pageimages",
                    "exintro": True,
                    "explaintext": True,
                    "titles": title,
                    "pithumbsize": 400
                }

                details_res = requests.get(details_url, params=details_params).json()
                pages = details_res["query"]["pages"]
                for _, page_data in pages.items():
                    famous_places.append({
                        "name": title,
                        "detail": page_data.get("extract", "No details available."),
                        "image": page_data.get("thumbnail", {}).get("source", "")
                    })

        return famous_places

    except Exception as e:
        return [{"error": str(e)}]

if __name__ == "__main__":
    info = get_country_info("India")
    print(info)