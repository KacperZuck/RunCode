# Scraper Brooks-Running.pl

## Description
This module is responsible for collecting product data from the [Brooks Running Poland](https://brooks-running.pl) website.  
It uses **Selenium** and **BeautifulSoup** to handle both static and dynamically loaded content.

## Features
- Extracts all product categories and subcategories
- Scrapes product details:
  - Name
  - SKU
  - Price
  - Sizes (with availability detection)
  - Description
  - Additional attributes (from product table)
- Supports paginated categories
- Saves data to structured JSON files:
  - `results/categories.json`
  - `results/products.json`