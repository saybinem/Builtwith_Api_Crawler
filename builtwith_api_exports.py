# encoding=utf8
import os
import logging
import json, csv
import sys
import argparse
import tldextract

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.dirname(os.path.abspath(__file__))))
)# - root_dir is fnb-backend directory
sys.path.append(root_dir)
# print root_dir
from builtwith_api import BuiltWith


logging.basicConfig(
	format='[%(asctime)s > %(module)s:%(lineno)d %(levelname)s]:%(message)s',
	level=logging.INFO, datefmt='%m/%d/%Y %I:%M:%S %p',
)

__usage__ = """
	python builtwith_api_exports.py
		-k "Builtwith Api Key"
		-i /path/to/in.csv
		-o /path/to/out.csv
		-t "technology1, technology2, technology3"
		-s, true/False
	"""


def is_tech_used_in_builtwith_api(response, technology):

		response = response or ""
		if not technology:
			technology = ""
			error = "technology not provided"
		return technology.lower().strip() in str(response).lower()


def export_builtwith_api_techs(input_csv, output_csv, key, technologies=[], save_content=False):

	technologies = technologies or []
	queries = list( csv.DictReader(open(input_csv)) )
	t_lines = len(queries)
	pt = progress_timer(description= 'export_builtwith_api_techs', n_iter=t_lines)
	writer = None
	BW = BuiltWith(key)
	
	for i,query in enumerate(queries):
		
		company_domain= query.get('company_domain','').strip()        
		serial_number = query.get('serial_number','').strip() or (i+1)
		row =  { "serial_number": serial_number, "company_domain": company_domain,
				 "bw_active_technologies_names":None, "bw_active_technologies_with_dates":None,
				 "bw_inactive_technologies":None, 'Errors': None
			}

		logging.info('\n{0}\nserial_number:{1}/{2} company_domain:{3}\n{0}'.format('*'*10,i+1,t_lines, company_domain))

		row.update({"Is "+technology+" Used": None for  technology in technologies })

		if company_domain:

			tldextract_out = tldextract.extract(company_domain)		
			company_domain = ( tldextract_out.domain + "." + tldextract_out.suffix)

			response = BW.lookup(company_domain)

			row["Errors"] = response.get("Errors")
			if response.get("Errors"):
					logging.error(response.get("Errors"))

			if save_content:
				json_file =  os.path.join( os.path.dirname(input_csv), company_domain + ".json")
				with open( json_file, "w") as f:
					f.write(json.dumps(response))

			for technology in technologies:
				row["Is "+technology+" Used"] = is_tech_used_in_builtwith_api(response, technology)
				
			
			response_technologies = BW.lookup_technologies(response=response)

			# if response_technologies.get("technology_names"):
			# 	bw_technologies =  ",".join(response_technologies["technology_names"]).encode("utf-8")
			# else:
			# 	bw_technologies = None

			if response_technologies.get("active_technologies_list"):
				bw_active_technologies_names = [ "[{}]".format(t['Name'].encode("utf-8")) 
											 for t in response_technologies["active_technologies_list"]
										]
			else:
				bw_active_technologies_names = []

			row["bw_active_technologies_names"] = ", ".join(bw_active_technologies_names)

			if response_technologies.get("active_technologies_list"):
				bw_active_technologies_with_dates = [ "[{} (added:{})]".format(t['Name'].encode("utf-8"), t['FirstDetected']) 
											 for t in response_technologies["active_technologies_list"]
										]
			else:
				bw_active_technologies_with_dates = []

			row["bw_active_technologies_with_dates"] = ", ".join(bw_active_technologies_with_dates)

			if response_technologies.get("inactive_technologies_list"):
				bw_inactive_technologies = [ "[{} (added:{} dropped:{})]".format(t['Name'].encode("utf-8"), t['FirstDetected'], t['LastDetected']) 
											 for t in response_technologies["inactive_technologies_list"]
										]
			else:
				bw_inactive_technologies = []

			row["bw_inactive_technologies"] = ", ".join(bw_inactive_technologies)
			

		if i ==0:
			writer = csv.DictWriter(open(output_csv, 'w'), lineterminator='\n', fieldnames=row)
			writer.writeheader()
			writer.writerow(row)
		else:
			# print "row is >>> ", row
			writer.writerow(row)

		pt.update()
	pt.finish()


if __name__=='__main__':
	
	parser = argparse.ArgumentParser()
	parser._optionals.title = "Builtwith Api Tech Export"
	parser.add_argument('-i', '--input_csv', help="Input CSV")
	parser.add_argument('-o', '--output_csv', help='Output CSV')
	parser.add_argument('-t', '--technologies', help='Get Tech Used')
	parser.add_argument('-k', '--key', help='Builtwith Api Key')
	parser.add_argument('-s', '--save_content', help='Save Builtwith Data in File',
						 default="False", type= lambda v: str(v).lower() in ('yes', 'true', 't', 'y', '1')
						)
	args = parser.parse_args()

	logging.info("Input CSV -> {}".format(args.input_csv))
	logging.info("Output CSV -> {}".format(args.output_csv))
	logging.info("Builtwith Api Key -> {}".format(args.key))
	logging.info("Save Builtwith Data in File -> {}".format(args.save_content))

	
	if args.technologies:
		technologies = [ t.strip() for t in args.technologies.split(",") ]
		logging.info("Tech to Search -> {}".format(technologies))
	else:
		technologies = []
	
	if args.input_csv and args.output_csv and args.key:

		export_builtwith_api_techs(
			input_csv = args.input_csv,
			output_csv = args.output_csv,
			technologies = technologies,
			save_content = args.save_content,
			key = args.key
		)
	else:
		logging.error("INVALID / Bad or Missing Arguments")
		logging.info("USAGE: {}".format(__usage__))
