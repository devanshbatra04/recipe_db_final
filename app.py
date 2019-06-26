from flask import Flask, render_template, request, jsonify
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
def exec_ingre_query():
	print("lol")

def exec_query(name, region, Sub_region, page,ings,not_ings,recipe_ids,include_nutrBorders=None, dict_nut_boundaries={}):
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
	queryType = 1
	conditions = []
	if len(name):
		conditions.append("with keyword in its title" + str(name.strip()))
	if len(Sub_region):
		#actually country
		conditions.append("from cuisine " + str(Sub_region.strip()))
	if len(region):
		#actually country
		conditions.append("from continent " + str(region.strip()))
	# No region mapping yet to be included soon
	if len(ings):
		queryType = 2
		conditions.append("having " + str(ings.strip()))

	if len(not_ings):
		queryType = 3
		conditions.append("not having " + str(not_ings.strip()))

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
		"select * from recipes1 where Recipe_title like \"%{}%\" and Region like \"%{}%\" and Sub_region like \"%{}%\" {}".format(name, region, Sub_region, subq),
		"select * from recipes1 inner join ingredients on recipes1.Recipe_id = ingredients.Recipe_id where ingredient_name like \"%{}%\" and Recipe_title like \"%{}%\" and Sub_region like \"%{}%\" and Region like \"%{}%\" {}".format(ings, name, Sub_region, region, subq),
		"select * from recipes1 where recipe_id not in (select recipe_id from ingredients where ingredient_name = \" {}\") and recipe_id in ({})"
	]


	queries[2] = queries[2].format(not_ings, queries[1].replace("*", "recipes1.Recipe_id"))
	heading = "Showing all recipes " + (", ".join(conditions))
	query = queries[queryType-1]
	cur = con.cursor()
	cur.execute(query.replace("*", "count(*)"))
	print(query)
	rows=cur.fetchall()
	num_recipes = rows[0][0]
	con.close()


	con = sql.connect("recipe2-final.db")
	con.row_factory = sql.Row
	cur = con.cursor()
	cur.execute(query + limit)
	rows = cur.fetchall()
	for i in range(len(rows)):
	   r = dict(rows[i])
	   rows[i] = r
	# con.close()

	cur.execute("select * from ingredients where Recipe_id in (" + (query+limit).replace("*", "recipes1.Recipe_id as Recipe") +")")
	all_ing = [dict(k) for k in cur.fetchall()]
	cur.execute("select * from nutrients where Recipe_id in (" + (query+limit).replace("*", "recipes1.Recipe_id as Recipe") +")")
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
	return render_template('home.html', empty = "no")

@app.route('/recipedb/all_recipes', methods=['GET'])
def all_recipes():
	rows, heading, num_recipes = exec_query("", "", "", 1,"", "recipe_search")
	if len(rows) == 0:
		rows, heading, num_recipes = exec_query(name, region, Sub_region, 1, "recipe_search")
	page_num_list, to_delete = get_page_num_list(1, num_recipes)
	bold_num = get_bold_num(1, page_num_list)
	if(len(rows) == 0):
		return render_template("home.html", empty = "yes")
	return render_template("p.html",rows = rows, heading = heading, name = "", cuisine = "", region = "", pagenum = "1", page_num_info = page_num_list, boldbuttonnum = bold_num, to_delete = to_delete)

@app.route('/recipedb/search_recipe', methods = ['GET', 'POST'])
def search_recipe():
	# print("hello")
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
		# print("maakabhoda ")
		name = request.form.get('autocomplete_recipe') if request.form.get("autocomplete_recipe") else ""
		# print(1)

		Sub_region = request.form.get('autocomplete_cuisine') if request.form.get("autocomplete_cuisine") else ""
		# print(2)
		region = request.form.get('autocomplete_region') if request.form.get("autocomplete_region") else ""
		print(region)
		ings = request.form.get('autocomplete_ingredient') if request.form.get("autocomplete_ingredient") else ""
		# print(ings)
		not_ings = request.form.get('autocomplete_noningredient') if request.form.get("autocomplete_noningredient") else ""
		# print(5)
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

		print(request.form.get("dict_nut_json"))

		rows, heading, num_recipes = exec_query(name, region, Sub_region, page,ings,not_ings, "recipe_search", include_nutrBorders, dict_nut_boundaries)
		print(str(num_recipes) + " recipes found")

		if len(rows) == 0:
			page = int(page) - 1
			rows, heading, num_recipes = exec_query(name, region, Sub_region, page,ings,not_ings, "recipe_search")
		if page == 0:
			page = 1
		page_num_list, to_delete = get_page_num_list(page, num_recipes)
		bold_num = get_bold_num(page, page_num_list)
		if(len(rows) == 0):
			return render_template("home.html", empty = "yes")
		return render_template("list_recipes.html", rows = rows, heading = heading, name = name, cuisine = Sub_region, region = region, ings = ings,not_ings=not_ings, pagenum = page, page_num_info = page_num_list, boldbuttonnum = bold_num, to_delete = to_delete, include_nutrBorders=include_nutrBorders, dict_nut_boundaries=json.dumps(dict_nut_boundaries))


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
		cur.execute("select * from recipes1 where Recipe_title like '%" + name + "%'")
	elif (check == "Sub_region"):
		cur.execute("select * from recipes1 where Sub_region like '%" + name + "%'")
	elif (check == "Region"):
		cur.execute("select * from recipes1 where Region like '%" + name + "%'")
	elif (check == "Entity_alias"):
		cur.execute("select * from entities where Entity_alias like '%" + name + "%'")

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

	rows, heading, num_recipes = exec_query(name, region, Sub_region, page,ings,not_ings, "recipe_search")

	if len(rows) == 0:
		page = int(page) - 1
		rows, heading, num_recipes = exec_query(name, region, Sub_region, page,ings,not_ings, "recipe_search")
	if page == 0:
		page = 1
	page_num_list, to_delete = get_page_num_list(page, num_recipes)
	bold_num = get_bold_num(page, page_num_list)
   # if(len(rows) == 0):
   #    return render_template("home.html", empty = "yes")
	return render_template("list_recipes.html", rows = rows, heading = heading, name = name, cuisine = Sub_region, region = region, ings = ings,not_ings=not_ings, pagenum = page, page_num_info = page_num_list, boldbuttonnum = bold_num, to_delete = to_delete)

@app.route('/recipedb/search_subregion/<string:id>',  methods = ['GET', 'POST'])
def search_subregion(id):
	page = 1
	region = ""
	name = ""
	Sub_region = id
	ings=""
	not_ings=""

	rows, heading, num_recipes = exec_query(name, region, Sub_region, page,ings,not_ings, "recipe_search")

	if len(rows) == 0:
		page = int(page) - 1
		rows, heading, num_recipes = exec_query(name, region, Sub_region, page,ings,not_ings, "recipe_search")
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
	Recipe_id=list_args[2]
	name_Ingre=list_args[1]

# WRITE QUERY FOR THE CASE WHEN WE GET TO INGREDIENT PAGE FROM CATEGORY PAGE. AFTER CLICKING ON CAROUSELS.

	if ndb_id=="id":
		query=''
		heading=name_Ingre
	else:
		query='SELECT * from nutrients where ndb_id="' + ndb_id + '" AND Recipe_id="' + Recipe_id + '"'
		query1='SELECT DISTINCT Recipe_title from recipes1 where Recipe_id="' + Recipe_id + '"'
		query2='SELECT * from nutrients where Recipe_id="' + Recipe_id + '"ORDER BY RANDOM() LIMIT 1 '
		heading=name_Ingre

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
		cur.execute(query)
		curr.execute(query1)
		currr.execute(query2)
		row = cur.fetchall()
		print(row)
		row1 = currr.fetchall()
		print(row1)
		if len(row)== 0:
			row=row1


   # if(len(rows) == 0):
   #    return render_template("home.html", empty = "yes")
	return render_template("ingredient.html",row=row,heading=heading)

@app.route('/recipedb/search_recipeInfo/<string:id>',  methods = ['GET', 'POST'])
def search_recipeInfo(id):
	con = sql.connect("recipe2-final.db")
	con.row_factory = sql.Row
	query='SELECT * from recipes1 where Recipe_id="' + id + '"'
	heading="Nutritional Profile of Recipe " + id + " is "

	def dict_factory(cursor, row):
		d = {}
		for idx, col in enumerate(cursor.description):
			d[col[0]] = row[idx]
		return d
	con.row_factory = dict_factory
	cur = con.cursor()
	cur.execute(query)
	row = cur.fetchall()
	recipeSteps = "Recipe Steps are not available."

	con.row_factory = sql.Row
	cur = con.cursor()
	cur.execute("select * from ingredients where Recipe_id = " + id + "")
	all_ing = [dict(k) for k in cur.fetchall()]
	cur.execute("select [Recipe_id], [ndb_id], [Carbohydrate, by difference], [Energy], [Protein], [Total lipid (fat)] from nutrients where Recipe_id like '%" + id + "%'")
	all_nutr = [dict(k) for k in cur.fetchall()]
	# ids = [rows[i]["Recipe_id"] for i in range(len(rows))]
	print(all_nutr)
	con = sql.connect("recipe2-final.db")
	con.row_factory = sql.Row
	ndb = 0
	cur = con.cursor()
	curr = con.cursor()
	rows1 = [d for d in all_ing if str(d["Recipe_id"]) == str(id)]
	rows2 = [d for d in all_nutr if str(d["Recipe_id"]) == str(id)]

	ing_names = []

	for rp in rows1:
		dict_row = dict(rp)
		ndb_id = rp["ndb_id"]
		nutr = {
			"Carbohydrate, by difference": "-",
			"Energy": "-",
			"Protein": "-",
			"Total lipid (fat)": "-",
		}
		for rowl in rows2:
			if str(dict(rowl)["ndb_id"]) == str(ndb_id):
				nutr = dict(rowl)
				break
		dict_row["nutrient_info"] = nutr
		ing_names.append(dict_row)

	# rows[i]["Ingredients"] = ing_names
	if stepsJSON != {}:
		recipeSteps = next((x['steps'] for x in stepsJSON if x['Recipe_id'] == id), "Recipe Steps are not available.")

	return render_template("recipeInfo.html",row=row,heading=heading, instructions=recipeSteps, ing_names=ing_names)


@app.route('/recipedb/FAQ',  methods = ['GET', 'POST'])
def FAQ():
	return render_template("FAQ.html")

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
	query='SELECT * from unique_ingredients where Category="' + id + '"'
	heading="" + id + ""
	print(heading)


	def dict_factory(cursor, row):
		d = {}
		for idx, col in enumerate(cursor.description):
			d[col[0]] = row[idx]
		return d
	con.row_factory = dict_factory
	cur = con.cursor()
	cur.execute(query)
	row = cur.fetchall()
	print(row[0]['Ing_name'])
	title="lol"
	return render_template("category.html", row=row,heading=heading)
if __name__ == '__main__':
  app.run(debug=True)
