
import sys, os

if config['Send_Notification_Emails']:
  exception_notifier_conf = {
    'sender': config['Email']['Sender'],
    'receivers': config['ExceptionNotificationList'],
    'mail_server': config['Email']['SMTP_Server'] + ':' + str(config['Email']['SMTP_Port']),
    'password': config['Email']['Password']
  }
  en.enable(callback=email_error_message, both=True, **exception_notifier_conf)

def is_non_zero_file(fpath):
  return True if os.path.isfile(fpath) and os.path.getsize(fpath) > 0 else False

def sum_division_expenses(sorted_dictionary, division_totals):
  for filetype in sorted_dictionary:
    for entry in sorted_dictionary[filetype]:
      division_totals[filetype] += sorted_dictionary[filetype][entry][SUM]
  return division_totals

def open_and_read_input_file(filepath):
  if is_non_zero_file(filepath):
    input_file = open(filepath, 'rb')
    input_file_lines = input_file.readlines()
    input_file_lines_list = list(input_file_lines)
    return list(input_file_lines)
  else:
    if config['Send_Notification_Emails']:
      print 'No Transactions Processed, Empty Input File'
      email_empty_file_message()
      session.quit()
      sys.exit(1)
    else:
      print 'No Transactions Processed, Empty Input File'
      sys.exit(1)

def initialize_division_totals(divisions):
  totals = {}
  for division in divisions:
    totals[division] = {}
    totals[division]['FileType1'] = Decimal(0.0000)
    totals[division]['FileType2'] = Decimal(0.0000)
    totals[division]['FileType3'] = Decimal(0.0000)
  return totals

def email_control_totals(division_totals, file_control_total, file_batch_date, output_files_per_division):
  global session
  calculated_control_total = Decimal(0.0000)
  for division in division_totals:
    calculated_control_total += division_totals[division]['FileType1']
    calculated_control_total += division_totals[division]['FileType2']
    calculated_control_total += division_totals[division]['FileType3']
  if file_control_total != calculated_control_total:
    print "Control totals do not match"
    print "Control total in file:", file_control_total
    print "Calculated Control Total:", calculated_control_total
    if config['Send_Notification_Emails']:
      email_control_total_batch_date_data(config['ControlTotalNotificationList'], file_control_total, calculated_control_total, file_batch_date)
      session.quit()
    sys.exit(1)
  else:
    if config['Send_Notification_Emails']:
      for division_group in output_files_per_division:
        email_output_file_paths_to_managers(config['Divisions'][division_group][EMAILS], output_files_per_division[division_group], division_totals[division_group], division_group)
      email_control_total_batch_date_data(config['ControlTotalNotificationList'], file_control_total, calculated_control_total, file_batch_date, division_totals)
      session.quit()
    print "Ran Successfully, Output Files Created"
    sys.exit(0)

def main(input_filepath):
  initial_dictionary = { 'regular_expenses': {}, 'employee_reimbursements_cash_advance_reconciliations': {}, 'cash_advance_issuances': {} }
  sorted_dictionary  = { 'FileType1': {}, 'FileType2': {}, 'FileType3': {} }
  output_dictionary  = {}
  output_files_per_division = {}
  division_totals = initialize_division_totals(config['Divisions'])
  input_file_lines_list = open_and_read_input_file(input_filepath)
  file_batch_date = input_file_lines_list[0].split('|')[1]
  file_control_total = Decimal(input_file_lines_list[0].split('|')[3])

  for division_group in config['Divisions']:
    initial_dictionary = read_input(input_file_lines_list, config['Divisions'][division_group][DIVISION_GROUPS], initial_dictionary)
    sorted_dictionary  = filter_expense_records(initial_dictionary, sorted_dictionary)
    sorted_dictionary['FileType1'] = initial_dictionary['regular_expenses'].copy()
    division_totals[division_group] = sum_division_expenses(sorted_dictionary, division_totals[division_group])
    output_file_list = []
    for filetype in sorted_dictionary:
      output_dictionary = populate_output_dict(sorted_dictionary[filetype], output_dictionary, filetype)
      for year_case in output_dictionary:
        for fiscal_year in output_dictionary[year_case]:
          output_rows = produce_output_rows(output_dictionary[year_case][fiscal_year], year_case, filetype)
          output_file_list.append(write_output_file(output_rows, division_group, filetype, fiscal_year, file_batch_date, config['Output_Path'] + file_batch_date + "\\" + division_group + "\\"))
      sorted_dictionary[filetype].clear()
      output_dictionary.clear()
    initial_dictionary['regular_expenses'].clear()
    initial_dictionary['employee_reimbursements_cash_advance_reconciliations'].clear()
    initial_dictionary['cash_advance_issuances'].clear()
    if len(output_file_list) > 0:
      output_files_per_division[division_group] = output_file_list
  email_control_totals(division_totals, file_control_total, file_batch_date, output_files_per_division)


if __name__ == "__main__":
  main(sys.argv[1])