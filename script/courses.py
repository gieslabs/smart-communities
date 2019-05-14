#!/home/marketlab/anaconda3/bin/python3
# -*- coding: utf-8 -*-
#
# Created on Wed Apr 19 09:42:29 2017
# @author: jlroo
#

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import re
import time


def create_url(website, year, term, course, section):
    url = website + "/" + year + "/" + term + "/" + course + "/" + section
    return {"url": url, "year": year, "term": term, "course": course, "section": section}


def courses_urls(path):
    gpa = pd.read_csv(path)
    gpa_group = gpa.groupby(["Year" , "Term" , "Subject"]).Number.unique()
    courses = []
    for k in gpa_group.keys():
        year = k[0]
        term = k[1]
        course = k[2]
        for i in gpa_group[k]:
            courses.append(create_url(website, str(year), term, course, str(i)))
    df = pd.DataFrame.from_dict(courses)
    return df


if __name__ == '__main__':
    chrome_options = webdriver.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument('headless')
    chrome_options.add_argument('window-size=1920x1080');
    driver = webdriver.Chrome("/home/marketlab/.local/bin/chromedriver",options=chrome_options)
    courses = pd.read_csv("data/courses-details.csv")
    courses_uiuc = []
    for index, row in courses.iterrows():
        try:
            driver.get(row["url"])
            driver.find_element_by_id("collapseAllTR").click()
            title = driver.find_element_by_class_name("app-label").text
            title = title.lower().replace(" " , "_")
            course_info = driver.find_element_by_id("app-course-info")
            course_info = course_info.find_elements_by_tag_name("p")[-1].text
            html = driver.find_element_by_class_name("dataTable").get_attribute("outerHTML")
            html = re.sub('<span class="hide">[0-9]{4}</span>' , "" , html)
            df = pd.read_html(html)[0]
            df.columns = [i.lower() for i in df.columns]
            df = df[['crn', 'type', 'section', 'time', 'day', 'location', 'instructor']]
            df = df[["Online" not in i for i in df.type]]
            df.time = [i.replace("ARRANGED","") for i in df.time]
            if df.size == 0:
                continue
            else:
                times = df.time.tolist()
                if any([len(i)>20 for i in times]) or any([i=="" for i in times]):
                    continue
                else:
                    start = []
                    end = []
                    for i in times:
                            start.append(i.split(" - ")[0])
                            end.append(i.split(" - ")[1])
                    df["time_start"] = pd.to_datetime(start , format='%I:%M%p').time
                    df["time_end"] = pd.to_datetime(end , format='%I:%M%p').time
                    df["course_tile"] = title
                    df["course_subject"] = str(row["course"]) 
                    df["course_number"] = str(row["section"])
                    df["course_term"] = row["term"]
                    df["course_year"] = str(row["year"])
                    df["course_info"] = course_info
                    df["course_schedule"] = row["url"]
                    df["course_type"] = df["type"]
                    df["course_day"] = df["day"]
                    df["course_section"] = df["section"]
                    col_names = ['crn', 'course_subject', 'course_number', 'course_section',
                                 'course_type', 'course_day', 'time_start', 'time_end', 'location',
                                 'course_term', 'course_year', 'instructor', 'course_tile',
                                 'course_info', 'course_schedule']
                    df = df[col_names]
                    courses_uiuc.append(df)
                    time.sleep(0.5)
        except NoSuchElementException:
            pass
    uiuc_courses = pd.concat(courses_uiuc)
    uiuc_courses.to_csv("data/uiuc-courses.csv", index=None)
    driver.close()
