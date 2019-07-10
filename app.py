from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3 as sql
import json
app = Flask(__name__, static_folder="recipedb")

stepsJSON = {}
try:
	with open("all-steps.json") as jsonfile:
		stepsJSON = json.load(jsonfile)
except:
	print("instruction json file issue ig");

def get_page_num_list(page, num_recipes):
	num_pages = num_recipes // 20
	if num_pages == 7:
	   return ["1", "2", "3", "4", "5", "6", "7"], 0
	elif num_pages < 7:
	   page_list = []
	   if num_pages == 0:
		   return ["1", "...", "...", "...", "...", "...", "..."], 7
	   c = 0
	   for i in range(1, num_pages + 1):
		   page_list.append(str(i))
	   for i in range(num_pages + 1, 8):
		   page_list.append("...")
		   c += 1
	   return page_list, c
	else:
	   if int(page) <= 5:
		   return ["1", "2", "3", "4", "5", "...", str(num_pages)], 0
	   elif int(page) >= num_pages - 4:
		   return ["1", "...", str(num_pages - 4), str(num_pages - 3), str(num_pages - 2), str(num_pages - 1), str(num_pages)], 0
	   else:
		   return ["1", "...", str(int(page)-1), str(int(page)), str(int(page)+1), "...", str(num_pages)], 0

def get_bold_num(page, page_num_list):
	index = page_num_list.index(str(page))
	bold_num = ""
	if index == 0:
		bold_num = "first"
	elif index == 1:
		bold_num = "second"
	elif index == 2:
		bold_num = "third"
	elif index == 3:
		bold_num = "fourth"
	elif index == 4:
		bold_num = "fifth"
	elif index == 5:
		bold_num = "sixth"
	else:
		bold_num = "seventh"
	return bold_num

#function to query for Ingredients

def exec_query(name, region, Sub_region, page,ings,not_ings, category, not_category, recipe_ids,include_nutrBorders=None, dict_nut_boundaries={}):
	print("hahahahaha")
	limit = " LIMIT 20 OFFSET " + str(((int(page)-1) * 20))
	con = sql.connect("recipe2-final.db")
	con.row_factory = sql.Row
	name=name.lower()
	region=region.lower()
	Sub_region=Sub_region.lower()
	page=page
	ings=ings.lower()
	not_ings=not_ings.lower()
	result = ings.split(',')
	ings= result[0]
	result1 = not_ings.split(',')
	not_ings= result1[0]
	query = ""
	heading = ""
	import time
	start = time.time()
	if (len(recipe_ids)==0):
		rows = []
		heading = ""
		num_recipes = 0
		return rows, heading, num_recipes

	#Query for recipeTable
	queryType = 0
	conditions = []
	v = False
	d=False
	if len(name):
		conditions.append("with " + str(name.strip())+ " keyword in its title")
		queryType = 1
		v = True


	if len(region):
		#actually country
		conditions.append("from " + str(region.strip()) + " cuisine")
		queryType = 1
		v = True
		d= True

	if len(Sub_region):
		#actually country
		if d==True :
			x=len(conditions)
			conditions.pop((x-1))
		conditions.append("from " + str(Sub_region.strip()) + " cuisine")
		queryType = 1
		v = True

	# No region mapping yet to be included soon
	if len(ings):
		queryType = 2
		conditions.append("having " + str(ings.strip()))
		v = True

	r = queryType
	if len(not_ings):
		queryType = 3
		conditions.append("not having " + str(not_ings.strip()))

	if len(category):
		if queryType == 0:
			queryType = 4
		conditions.append("having ingredients from " + str(category.strip())+ " category")
	if len(not_category):
		if queryType == 0:
			queryType = 4
		conditions.append("not having ingredients from " + str(not_category.strip())+ " category")
	conditions = list(map(lambda x: x.strip(), conditions))

	subq = ""
	if include_nutrBorders == "on":
		protein_min = dict_nut_boundaries['protein_min']
		protein_max = dict_nut_boundaries['protein_max']
		fat_min = dict_nut_boundaries['fat_min']
		fat_max = dict_nut_boundaries['fat_max']
		energy_min = dict_nut_boundaries['energy_min']
		energy_max = dict_nut_boundaries['energy_max']
		carb_min = dict_nut_boundaries['carb_min']
		carb_max = dict_nut_boundaries['carb_max']
		subq = "and \"Protein(g)\" BETWEEN {} and {} and \"Energy(kcal)\" BETWEEN {} and {} and \"Totallipid(fat)(g)\" BETWEEN {} and {} and \"Carbohydratebydifference(g)\" BETWEEN {} and {}".format(int(float(protein_min)), int(float(protein_max)), int(float(energy_min)), int(float(energy_max)), int(float(fat_min)), int(float(fat_max)), int(float(carb_min)), int(float(carb_max)))

	queries = [
		"select Distinct(recipes2.Recipe_id) from recipes2 where Recipe_title like \"%{}%\" and Region like \"%{}%\" and Sub_region like \"%{}%\" {}".format(name, region, Sub_region, subq),
		"select Distinct(recipes2.Recipe_id) from recipes2 natural join ingredients where ingredient_name like \"%{}%\" and Recipe_title like \"%{}%\" and Sub_region like \"%{}%\" and Region like \"%{}%\" {}".format(ings, name, Sub_region, region, subq),
		"select Distinct(recipes2.Recipe_id) from recipes2 where recipe_id not in (select recipe_id from ingredients where ingredient_name = \" {}\"){}",
		"select DISTINCT(Recipe_id) from ingredients where Ing_id in (select Ing_ID from unique_ingredients where " + ("unique_ingredients.\"Category-F-DB\" like \"{}\"".format(category) if len(category) else "")+ (" and " if (len(category) and len(not_category)) else "") + ("Ing_id not in (select Ing_ID from unique_ingredients where unique_ingredients.\"Category-F-DB\" like \"{}\")".format(not_category) if len(not_category) else "") + ")"

	]

	if r == 0:
		smallQ = ""
	elif r==2 and len(name) == 0 and len(region) == 0 and len(Sub_region) == 0:
		smallQ = "select Distinct(Recipe_id) from recipes2 natural join ingredients where ingredient_name like \"%{}%\"".format(ings)
	else:
		smallQ = queries[r-1]
	queries[2] = queries[2].format(not_ings, "" if v == False else " and recipe_id in ({})".format(smallQ))

	if queryType == 0:
		queryType = 1

	heading = "Showing all recipes " + (", ".join(conditions))
	query = queries[queryType-1]


	queryf = "Select * from recipes2 where recipes2.Recipe_id in({})".format(query)
	cur = con.cursor()
	print(query)
	if queryType < 4:
		# print(query)
		cur.execute(query.replace("Distinct(recipes2.Recipe_id)", "count(Distinct(recipes2.Recipe_id))"))
	else:
		cur.execute(query.replace("DISTINCT(Recipe_id)", "count(Distinct(ingredients.Recipe_id))"))
	# print(query)
	rows=cur.fetchall()
	num_recipes = rows[0][0]
	con.close()


	con = sql.connect("recipe2-final.db")
	con.row_factory = sql.Row
	cur = con.cursor()
	cur.execute(queryf + limit)
	rows = cur.fetchall()
	for i in range(len(rows)):
	   r = dict(rows[i])
	   rows[i] = r
	# con.close()

	cur.execute("select * from ingredients where Recipe_id in (" + (query+limit) +")")
	all_ing = [dict(k) for k in cur.fetchall()]
	cur.execute("select * from 'nutrients-new' where Recipe_id in (" + (query+limit) +")")
	all_nutr = [dict(k) for k in cur.fetchall()]
	ids = [rows[i]["Recipe_id"] for i in range(len(rows))]
	for i in range(len(ids)):
		con = sql.connect("recipe2-final.db")
		con.row_factory = sql.Row
		ndb=0
		cur = con.cursor()
		curr = con.cursor()
		rows1 = [d for d in all_ing if str(d["Recipe_id"]) == str(ids[i])]
		rows2 = [d for d in all_nutr if str(d["Recipe_id"]) == str(ids[i])]
		# print(rows1)
		# print(rows2)

		ing_names = []

		for row in rows1:
			dict_row = dict(row)
			ndb_id = row["ndb_id"]
			nutr = None
			for rowl in rows2:
				if str(dict(rowl)["ndb_id"]) == str(ndb_id):
					nutr = dict(rowl)
					break
			dict_row["nutrient_info"] = nutr
			ing_names.append(dict_row)
		rows[i]["Ingredients"] = ing_names

	end = time.time()
	time_taken = end - start
	print('Time: ',time_taken)

	return rows, heading, num_recipes


@app.route('/recipedb/load_Calstats', methods=['GET', 'POST'])
def load_Calstats():
	return render_template('cal_serv.html')

@app.route('/recipedb/conmap', methods=['GET', 'POST'])
def load_conceptMap():
	return render_template('concept-map.html')

@app.route('/recipedb/load_Ingstats', methods=['GET', 'POST'])
def load_Ingstats():
	return render_template('recipe_size.html')

@app.route('/recipedb/')
def home():
	import datetime
	dayOfYear = datetime.datetime.today().timetuple().tm_yday
	con = sql.connect("recipe2-final.db")
	con.row_factory = sql.Row

	query='select * from recipes2 where img_url like "%img.snd%" limit 1 offset ' + str(dayOfYear)
	print(query)
	# heading="Nutritional Profile of Recipe " + id + " is "


	cur = con.cursor()
	cur.execute(query)
	row=cur.fetchone()
	print(row)
	if row['img_url']=="https://geniuskitchen.sndimg.com/gk/img/gk-shareGraphic.png" or row['img_url']=="https://images.media-allrecipes.com/images/79591.png":
		row['img_url']="/recipedb/static/recipe_temp.jpg"
	print(row['img_url'])
	return render_template('home.html', row=row,empty = "no")

@app.route('/recipedb/all_recipes', methods=['GET'])
def all_recipes():
	rows, heading, num_recipes = exec_query("", "", "", 1,"","","", "recipe_search")
	if len(rows) == 0:
		rows, heading, num_recipes = exec_query(name, region, Sub_region, 1,"","", "recipe_search")
	page_num_list, to_delete = get_page_num_list(1, num_recipes)
	bold_num = get_bold_num(1, page_num_list)
	if(len(rows) == 0):
		return render_template("home.html", empty = "yes")
	return render_template("p.html",rows = rows, heading = heading, name = "", cuisine = "", region = "", pagenum = "1", page_num_info = page_num_list, boldbuttonnum = bold_num, to_delete = to_delete)

@app.route('/recipedb/search_recipe', methods = ['GET', 'POST'])
def search_recipe():
	try:
		if request.method == 'POST':
			# print("ee ka hai")
			page = 1
			# print( "lol")
			pageinfo = request.form['page']

			if len(pageinfo) != 0:
				if int(pageinfo) < 1:
					page = 1
				else:
					page = request.form['page']
			name = request.form.get('autocomplete_recipe') if request.form.get("autocomplete_recipe") else ""
			# print(1)

			Sub_region = request.form.get('autocomplete_cuisine') if request.form.get("autocomplete_cuisine") else ""
			# print(2)
			region = request.form.get('autocomplete_region') if request.form.get("autocomplete_region") else ""
			ings = request.form.get('autocomplete_ingredient') if request.form.get("autocomplete_ingredient") else ""
			# print(ings)
			not_ings = request.form.get('autocomplete_noningredient') if request.form.get("autocomplete_noningredient") else ""
			# print(5)
			if len(ings) and ings.replace(",", "").strip().lower() == not_ings.replace(",", "").strip().lower():
				return render_template("home.html", empty="yes")
			category = request.form.get('autocomplete_category') if request.form.get("autocomplete_category") else ""
			notcategory = request.form.get('autocomplete_noncategory') if request.form.get("autocomplete_noncategory") else ""
			if len(category) and category.replace(",", "").strip().lower() == notcategory.replace(",", "").strip().lower():
				return render_template("home.html", empty="yes")

			include_nutrBorders = request.form.get('nutrRangeOn')
			# print(6)
			dict_nut_boundaries = {}
			if request.form.get("dict_nut_json") and request.form.get("dict_nut_json") != "{}":
				dict_nut_boundaries = json.loads(request.form.get("dict_nut_json"))

			else:
				dict_nut_boundaries = {
					"protein_min" : request.form.get('proteinMin'),
					"protein_max" : request.form.get('proteinMax'),
					"fat_min" : request.form.get('fatMin'),
					"fat_max" : request.form.get('fatMax'),
					"energy_min" : request.form.get('energyMin'),
					"energy_max" : request.form.get('energyMax'),
					"carb_min" : request.form.get('carbMin'),
					"carb_max" : request.form.get('CarbMax')
				}

			# print(request.form.get("dict_nut_json"))

			rows, heading, num_recipes = exec_query(name, region, Sub_region, page,ings,not_ings,category, notcategory, "recipe_search", include_nutrBorders, dict_nut_boundaries)
			# print(str(num_recipes) + " recipes found")

			if len(rows) == 0:
				page = int(page) - 1
				rows, heading, num_recipes = exec_query(name, region, Sub_region, page,ings,not_ings,category, notcategory, "recipe_search")
			if page == 0:
				page = 1
			page_num_list, to_delete = get_page_num_list(page, num_recipes)
			bold_num = get_bold_num(page, page_num_list)
			if(len(rows) == 0):
				return render_template("home.html", empty = "yes")
			return render_template("list_recipes.html", rows = rows, heading = heading, name = name, cuisine = Sub_region, region = region, ings = ings,not_ings=not_ings, pagenum = page, page_num_info = page_num_list, boldbuttonnum = bold_num, to_delete = to_delete, include_nutrBorders=include_nutrBorders, dict_nut_boundaries=json.dumps(dict_nut_boundaries), category=category, not_category=notcategory)
	except:
		return render_template("home.html", empty="yes")

@app.route('/recipedb/autocomplete_recipe', methods=['GET'])
def autocomplete_recipe():
	rr = auto_query("Recipe_title")
	return jsonify(matching_results=rr)

@app.route('/recipedb/autocomplete_cuisine', methods=['GET'])
def autocomplete_cuisine():
	rr = auto_query("Sub_region")
	return jsonify(matching_results=rr)

@app.route('/recipedb/autocomplete_region', methods=['GET'])
def autocomplete_region():
	rr = auto_query("Region")
	return jsonify(matching_results=rr)

@app.route('/recipedb/autocomplete_ingredient', methods=['GET'])
def autocomplete_ingredient():
	rr = auto_query("Entity_alias")
	return jsonify(matching_results=rr)
@app.route('/recipedb/autocomplete_noningredient', methods=['GET'])
def autocomplete_noningredient():
	rr = auto_query("Entity_alias")
	return jsonify(matching_results=rr)


def auto_query(check):
	name = request.args.get('q')
	con = sql.connect("recipe2-final.db")
	con.row_factory = sql.Row

	cur = con.cursor()

	if (check == "Recipe_title"):
		cur.execute("select * from recipes2 where Recipe_title like '%" + name + "%'")
	elif (check == "Sub_region"):
		cur.execute("select * from recipes2 where Sub_region like '%" + name + "%'")
	elif (check == "Region"):
		cur.execute("select * from recipes2 where Region like '%" + name + "%'")

	rows = cur.fetchall()
	rows = [dict(row) for row in rows]
	rr = []
	for row in rows:
		rr.append(row[check])
	rr = list(set(rr))
	return rr


@app.route('/recipedb/search_region/<string:id>',  methods = ['GET', 'POST'])
def search_region(id):
	page = 1
	region = id
	name = ""
	Sub_region = ""
	ings=""
	not_ings=""

	rows, heading, num_recipes = exec_query(name, region, Sub_region, page,ings,not_ings,"","", "recipe_search")

	if len(rows) == 0:
		page = int(page) - 1
		rows, heading, num_recipes = exec_query(name, region, Sub_region, page,ings,not_ings,"","", "recipe_search")
	if page == 0:
		page = 1
	page_num_list, to_delete = get_page_num_list(page, num_recipes)
	bold_num = get_bold_num(page, page_num_list)
   # if(len(rows) == 0):
   #    return render_template("home.html", empty = "yes")
	return render_template("list_recipes.html", rows = rows, heading = heading, name = name, cuisine = Sub_region, region = region, ings = ings,not_ings=not_ings, pagenum = page, page_num_info = page_num_list, boldbuttonnum = bold_num, to_delete = to_delete)

@app.route('/recipedb/ingredient/<string:name>',  methods = ['GET', 'POST'])
def redirect_to_ingredient(name):
	con = sql.connect("recipe2-final.db")
	con.row_factory = sql.Row
	cur = con.cursor()
	cur.execute("select Ing_id from unique_ingredients where Ing_name like \"{}\"".format(name))
	row = cur.fetchone()
	t = "a_b_" + str(row[0])
	# print(url_for('search_ingre', id=))
	return redirect((url_for('search_ingre', id=t)))


# @app.route('/recipedb/ingredient/<string:name>',  methods = ['GET', 'POST'])
# def redirect_to_home(name):
# 	con = sql.connect("recipe2-final.db")
# 	con.row_factory = sql.Row
# 	cur = con.cursor()
# 	cur.execute("select Ing_id from unique_ingredients where Ing_name like \"{}\"".format(name))
# 	row = cur.fetchone()
# 	t = "a_b_" + str(row[0])
# 	# print(url_for('search_ingre', id=))
# 	return redirect((url_for('home'))
#
# @app.errorhandler(werkzeug.exceptions.BadRequest)
# def handle_bad_request(e):
#     return ('bad request!', 400)

@app.route('/recipedb/search_subregion/<string:id>',  methods = ['GET', 'POST'])
def search_subregion(id):
	page = 1
	region = ""
	name = ""
	Sub_region = id
	ings=""
	not_ings=""

	rows, heading, num_recipes = exec_query(name, region, Sub_region, page,ings,not_ings,"","", "recipe_search")

	if len(rows) == 0:
		page = int(page) - 1
		rows, heading, num_recipes = exec_query(name, region, Sub_region, page,ings,not_ings,"","", "recipe_search")
	if page == 0:
		page = 1
	page_num_list, to_delete = get_page_num_list(page, num_recipes)
	bold_num = get_bold_num(page, page_num_list)
   # if(len(rows) == 0):
   #    return render_template("home.html", empty = "yes")
	return render_template("list_recipes.html", rows = rows, heading = heading, name = name, cuisine = Sub_region, region = region, ings = ings,not_ings=not_ings, pagenum = page, page_num_info = page_num_list, boldbuttonnum = bold_num, to_delete = to_delete)

@app.route('/recipedb/search_ingre/<string:id>',  methods = ['GET', 'POST'])
def search_ingre(id):
	con = sql.connect("recipe2-final.db")
	conn = sql.connect("recipe2-final.db")
	connn = sql.connect("recipe2-final.db")
	con.row_factory = sql.Row
	conn.row_factory = sql.Row
	connn.row_factory = sql.Row
	list_args=id.split('_')
	ndb_id=list_args[0]
	# Recipe_id=list_args[2]
	ingredient_id=list_args[2]
	name_Ingre=list_args[1]

	def dict_factory(cursor, row):
		d = {}
		for idx, col in enumerate(cursor.description):
			d[col[0]] = row[idx]
		return d
	con.row_factory = dict_factory
	connn.row_factory = dict_factory
	cur = con.cursor()
	curr = conn.cursor()
	currr = connn.cursor()
	query = "select * from unique_ingredients where Ing_ID = '{}'".format(ingredient_id)
	cur.execute(query)
	curr.execute("select * from USDA_100_grams natural join (select ndb_id, state, ingredient_name, count(*) as value_occurence from ingredients where Ing_ID = '{}' group by ndb_id,state, ingredient_name having count(ingredient_name)=1 order by value_occurence DESC limit 20)".format(ingredient_id))
	generic_ingredient_info = cur.fetchone()
	forms_info = [dict(k) for k in curr.fetchall()]
	currr.execute("select * from recipes2 natural join ingredients where ingredients.Ing_ID = '{}' group by Recipe_id limit 20".format(ingredient_id))
	recipes_info = [dict(k) for k in currr.fetchall()]

	return render_template("ingredient.html",generic_ingredient_info=generic_ingredient_info, forms_info=forms_info, recipes_info=recipes_info)

@app.route('/recipedb/search_recipeInfo/<string:id>',  methods = ['GET', 'POST'])
def search_recipeInfo(id):
	con = sql.connect("recipe2-final.db")
	con.row_factory = sql.Row
	query='SELECT * from recipes2 where Recipe_id="' + id + '"'
	heading="Nutritional Profile of Recipe " + id + " is "

	def dict_factory(cursor, row):
		d = {}
		for idx, col in enumerate(cursor.description):
			d[col[0]] = row[idx]
		return d
	con.row_factory = dict_factory
	cur = con.cursor()
	import time
	start = time.time()
	cur.execute(query)
	row = cur.fetchall()
	recipeSteps = "Recipe Steps are not available."

	con.row_factory = sql.Row
	cur = con.cursor()
	cur.execute("select * from ingredients where Recipe_id = '" + id + "'")
	all_ing = [dict(k) for k in cur.fetchall()]
	end = time.time()
	time_taken = end - start
	print('Time1: ',time_taken)
	cur.execute("select [Recipe_id], [ndb_id], [Carbohydrate, by difference (g)], [Energy (kcal)], [Protein (g)], [Total lipid (fat) (g)] from 'nutrients-new' where Recipe_id = '" + id + "'")
	all_nutr = [dict(k) for k in cur.fetchall()]
	con = sql.connect("recipe2-final.db")
	con.row_factory = sql.Row
	try:
		cur.execute(
			"select * from 'Recipe_nutrition_full' where Recipe_id = '" + id + "'")
		full_profile = dict(cur.fetchone())
	except:
		full_profile = {}
	try:
		rows1 = [d for d in all_ing if str(d["Recipe_id"]).strip() == str(id).strip()]
	except:
		rows1 = []
	try:
		rows2 = [d for d in all_nutr if str(d["Recipe_id"]).strip() == str(id).strip()]
	except:
		rows2 = []

	ing_names = []

	for rp in rows1:
		dict_row = dict(rp)
		ndb_id = rp["ndb_id"]
		nutr = {
			"Carbohydrate, by difference (g)": "N/A",
			"Energy (kcal)": "N/A",
			"Protein (g)": "N/A",
			"Total lipid (fat) (g)": "N/A",
		}
		for rowl in rows2:
			if str(dict(rowl)["ndb_id"]) == str(ndb_id):
				nutr = dict(rowl)
				break
		dict_row["nutrient_info"] = nutr
		ing_names.append(dict_row)
		# print(ing_names)

	# rows[i]["Ingredients"] = ing_names
	if stepsJSON != {}:
		recipeSteps = next((x['steps'] for x in stepsJSON if x['Recipe_id'] == id), "Recipe Steps are not available.")
	if row[0]['img_url']=="https://geniuskitchen.sndimg.com/gk/img/gk-shareGraphic.png" or row[0]['img_url']=="https://images.media-allrecipes.com/images/79591.png":
		row[0]['img_url']="/recipedb/static/recipe_temp.jpg"

	# print(row[0]['img_url'])
	import re
	useCase = re.findall('[A-Z][^A-Z]*', row[0]['Source'])
	print(useCase)
	row[0]['Source']= useCase[0] + " " + useCase[1] 
	print(row[0]['Source'])
	x=row[0]['url'].split('/')
	# print(x)
	if x[0]=="http:":
		x[0]='https:'
		x='/'.join(x)
		row[0]['url']=x

	return render_template("recipeInfo.html",row=row,heading=heading, instructions=recipeSteps, ing_names=ing_names, full_profile=full_profile)


@app.route('/recipedb/FAQ',  methods = ['GET', 'POST'])
def FAQ():
	return render_template("FAQ.html")

@app.route('/recipedb/receptors',  methods = ['GET', 'POST'])
def Receptors():
	return render_template("receptors.html")

@app.route('/recipedb/contactUs',  methods = ['GET', 'POST'])
def ContactUs():
	return render_template("contactUs.html")

@app.route('/recipedb/howto',  methods = ['GET', 'POST'])
def how():
	return render_template("howto.html")

@app.route('/recipedb/Stats',  methods = ['GET', 'POST'])
def stats():
	return render_template("stats.html")

@app.route('/recipedb/category/<string:id>',  methods = ['GET', 'POST'])
def category(id):
	con = sql.connect("recipe2-final.db")
	con.row_factory = sql.Row
	query='SELECT * from unique_ingredients where "Category-F-DB" like "' + id + '" and NOT aliases="" LIMIT 5'
	query1='SELECT * from unique_ingredients where "Category-F-DB" like "' + id + '" and NOT aliases="" LIMIT 20'
	# print(query)
	heading="" + id + ""
	# print(heading)


	def dict_factory(cursor, row):
		d = {}
		for idx, col in enumerate(cursor.description):
			d[col[0]] = row[idx]
		return d
	con.row_factory = dict_factory
	cur = con.cursor()
	cur.execute(query)
	row = cur.fetchall()
	# print(row[0])
	cur.execute(query1)
	row2=cur.fetchall()

	query2='SELECT * from recipes2 where Recipe_id in (Select Recipe_id from ingredients where ingredient_name="' + row[0]['Ing_name'] + '" OR ingredient_name="' + row[1]['Ing_name'] + '" OR ingredient_name="' + row[2]['Ing_name'] + '" OR ingredient_name="' + row[3]['Ing_name'] + '" LIMIT 21 )'
	cur.execute(query2)
	rec2=cur.fetchall()
	# print(rec2)
	show=len(rec2)

	queryimg='SELECT cat_Image from cat_Img where "Category" like "' + id + '"'
	cur.execute(queryimg)
	# print(queryimg)
	img=cur.fetchone()
	# print(img)
	return render_template("category.html", row=row,heading=heading,row2=row2,fin=rec2,img=img,show=show)
if __name__ == '__main__':
  app.run(debug=True)
