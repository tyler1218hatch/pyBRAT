# -------------------------------------------------------------------------------
# Name:        Collect Summary Products
# Purpose:     Collects any *.ai, *.png, or *.pdf files and automatically copies them
#              into the proper structure
#
# Author:      Braden Anderson
#
# Created:     12/2018
# -------------------------------------------------------------------------------

import shutil
from SupportingFunctions import make_folder
import os
import xlsxwriter
import arcpy

def main(project_folder, stream_network, watershed_name, excel_file_name=None, output_folder=None):
    """
    Our main function
    :param project_folder: The BRAT Project that we want to collect the summary products for
    :return:
    """
    if excel_file_name is None:
        excel_file_name = "BRAT_Summary_Tables"
    if not excel_file_name.endswith(".xlsx"):
        excel_file_name += ".xlsx"
        
    
    summary_prods_folder = os.path.join(project_folder, "SummaryProducts")
    table_folder = make_folder(summary_prods_folder, "SummaryTables")

    if output_folder is None:
        output_folder = table_folder
        
    create_folder_structure(project_folder, summary_prods_folder)

    if (stream_network.count(';')>0):
        stream_network = merge_networks(summary_prods_folder, stream_network)

    fields = [f.name for f in arcpy.ListFields(stream_network)]
    create_excel_file(excel_file_name, stream_network, output_folder, watershed_name, fields)


def split_multi_inputs(multi_input_parameter):
    """
    Splits an ArcMap Toolbox Multi-Value parameter into a Python list object.
    ArcMap Multi-Value inputs are semi-colon delimited text strings.
    """
    try:
        #Remove single quotes
        multi_input_parameter = multi_input_parameter.replace("'","")

        #split input tables by semicolon ";"
        return multi_input_parameter.split(";")
    except:
        raise Exception("Could not split multi-input")


def merge_networks(summary_prods_folder, stream_network):

    mergedFile = os.path.join(summary_prods_folder, "Merged.shp")
    toMerge= split_multi_inputs(stream_network)
    arcpy.CreateFeatureclass_management(summary_prods_folder, "Merged.shp", "POLYLINE", toMerge[0])
    arcpy.Append_management (toMerge, mergedFile, "NO_TEST")
    return mergedFile

    
def create_excel_file(excel_file_name, stream_network, output_folder, watershed_name, fields):
    workbook = xlsxwriter.Workbook(os.path.join(output_folder, excel_file_name))
    write_capacity_sheets(workbook, stream_network, watershed_name, fields)
    workbook.close()


def write_capacity_sheets(workbook, stream_network, watershed_name, fields):

    summary_worksheet = workbook.add_worksheet("Watershed Summary")
    write_summary_worksheet (summary_worksheet, stream_network, watershed_name, workbook, fields)
    if 'oCC_EX' in fields:
        exist_build_cap_worksheet = workbook.add_worksheet("Existing Dam Building Capacity")
        write_exist_build_cap_worksheet(exist_build_cap_worksheet, stream_network, watershed_name, workbook)
    else:
        arcpy.AddWarning("Existing dam building capacity worksheet could not be built because oCC_EX not in fields")
    if 'mCC_EX_CT' in fields:
        exist_complex_worksheet = workbook.add_worksheet("Existing Dam Complex Size")
        write_exist_complex_worksheet(exist_complex_worksheet, stream_network, watershed_name, workbook)
    else:
        arcpy.AddWarning("Existing dam complex size worksheet could not be built because mCC_EX_CT not in fields")
    if 'oCC_HPE' in fields:
        hist_build_cap_worksheet = workbook.add_worksheet("Historic Dam Building Capacity")
        write_hist_build_cap_worksheet(hist_build_cap_worksheet, stream_network, watershed_name, workbook)
    else:
        arcpy.AddWarning("Historic dam builiding capacity worksheet could not be built because oCC_HPE not in fields")
    if 'mCC_HPE_CT' in fields:
        hist_complex_worksheet = workbook.add_worksheet("Historic Dam Complex Size")
        write_hist_complex_worksheet(hist_complex_worksheet, stream_network, watershed_name, workbook)
    else:
        arcpy.AddWarning("Existing dam complex size worksheet could not be built because mCC_HPE_CT not in fields")
    if 'mCC_HPE_CT' in fields and 'mCC_EX_CT' in fields:
        hist_vs_exist_worksheet = workbook.add_worksheet("Existing vs. Historic Capacity")
        write_hist_vs_exist_worksheet(hist_vs_exist_worksheet, stream_network, watershed_name, workbook)
    else:
        arcpy.AddWarning("Existing vs. Historic worksheet could not be built because mCC_EX_CT or mCC_HPE_CT not in fields")
    if 'oPBRC_CR' in fields:
        cons_rest_worksheet = workbook.add_worksheet("Conservation Restoration")
        write_conservation_restoration(cons_rest_worksheet, stream_network, watershed_name, workbook)
    else:
        arcpy.AddWarning("Conservation restoration worksheet could not be built because oPBRC_CR not in fields")
    if 'oPBRC_UD' in fields:
        unsuitable_worksheet = workbook.add_worksheet("Unsuitable or Limited")
        write_unsuitable_worksheet(unsuitable_worksheet, stream_network, watershed_name, workbook)
    else:
        arcpy.AddWarning("Unsuitable/limited dam opportunities worksheet could not be built because oPBRC_UD not in fields")
    if 'oPBRC_UI' in fields:
        risk_worksheet = workbook.add_worksheet("Undesirable Dams")
        write_risk_worksheet(risk_worksheet, stream_network, watershed_name, workbook)
    else:
        arcpy.AddWarning("Risk worksheet could not be built because oPBRC_UI not in fields")
    if 'ConsVRest' in fields:
        strategies_worksheet = workbook.add_worksheet("Management Strategies")
        write_strategies_worksheet(strategies_worksheet, stream_network, watershed_name, workbook)
    else:
        arcpy.AddWarning("Strategies worksheet could not be built because ConsVRest not in fields")
    if 'BRATvSurv' in fields:
        validation_worksheet = workbook.add_worksheet("Predicted vs. Surveyed")
        write_validation_worksheet(validation_worksheet, stream_network, watershed_name, workbook)
    else:
        arcpy.AddWarning("Predicted vs. surveyed worksheet could not be built because BRATvSurv not in fields")
    if 'e_DamCt' in fields:
        electivity_worksheet = workbook.add_worksheet("Electivity Index")
        write_electivity_worksheet(electivity_worksheet, stream_network, watershed_name, workbook)
    else:
        arcpy.AddWarning("Electivity index could not be built because e_DamCt not in fields")
    


# Maggie's code
def make_capacity_table(output_network, mcc_hpe):
    brat_table = arcpy.da.TableToNumPyArray(output_network,
                                            ['iGeo_Len', 'mCC_EX_CT', 'oCC_EX', 'ExCategor', 'oCC_HPE', 'mCC_HPE_CT',
                                             'HpeCategor'], skip_nulls=True)
    tot_length = brat_table['iGeo_Len'].sum()
    total_ex_capacity = brat_table['mCC_EX_CT'].sum()
    total_hpe_capacity = brat_table[mcc_hpe].sum()
    capacity_table = []
    ex_pervasive = add_capacity_category(brat_table, 'Existing', 'Pervasive', tot_length)
    ex_frequent = add_capacity_category(brat_table, 'Existing', 'Frequent', tot_length)
    ex_occasional = add_capacity_category(brat_table, 'Existing', 'Occasional', tot_length)
    ex_rare = add_capacity_category(brat_table, 'Existing', 'Rare', tot_length)
    ex_none = add_capacity_category(brat_table, 'Existing', 'None', tot_length)
    hist_pervasive = add_capacity_category(brat_table, 'Historic', 'Pervasive', tot_length)
    hist_frequent = add_capacity_category(brat_table, 'Historic', 'Frequent', tot_length)
    hist_occasional = add_capacity_category(brat_table, 'Historic', 'Occasional', tot_length)
    hist_rare = add_capacity_category(brat_table, 'Historic', 'Rare', tot_length)
    hist_none = add_capacity_category(brat_table, 'Historic', 'None', tot_length)


# Maggie's code
def add_capacity_category(brat_table, type, category, tot_length):
    if type == 'Existing':
        cat_tbl = brat_table[brat_table['ExCategor'] == category]
    else:
        cat_tbl = brat_table[brat_table['HpeCategor'] == category]
    length = cat_tbl['iGeo_Len'].sum()
    length_km = length / 1000
    network_prop = 100 * length / tot_length
    est_dams = cat_tbl['mCC_EX_CT'].sum()
    return length, length_km, network_prop, est_dams


# Writing the side headers for complex size
def write_categories_complex(worksheet,watershed_name):
    column_sizeA = worksheet.set_column('A:A', column_calc (30, watershed_name))
    row = 2
    col = 0
    worksheet.write(row, col, "No Dams", column_sizeA)
    row += 1
    worksheet.write(row, col, "Single Dam")
    row += 1
    worksheet.write(row, col, "Small Complex (2-3 Dams)")
    row += 1
    worksheet.write(row, col, "Medium Complex (4-5 dams)")
    row += 1
    worksheet.write(row, col, "Large Complex (>5 dams)")
    row += 1
    worksheet.write(row, col, "Total")


# Writing the side headers for build capacity
def write_categories_build_cap(worksheet, watershed_name):
    column_sizeA = worksheet.set_column('A:A', column_calc (30, watershed_name))
    row = 2
    col = 0
    worksheet.write(row, col, "None: 0", column_sizeA)
    row += 1
    worksheet.write(row, col, "Rare: < 1")
    row += 1
    worksheet.write(row, col, "Occasional: 2 - 5")
    row += 1
    worksheet.write(row, col, "Frequent: 6 - 15 ")
    row += 1
    worksheet.write(row, col, "Pervasive: 16 - 40")
    row += 1
    worksheet.write(row, col, "Total")

def write_categories_hist_vs_exist(worksheet):
    row = 3
    col = 0
    worksheet.write(row, col, "Pervasive")
    row += 1
    worksheet.write(row, col, "Frequent")
    row += 1
    worksheet.write(row, col, "Occasional")
    row += 1
    worksheet.write(row, col, "Rare")
    row += 1
    worksheet.write(row, col, "None")
    row += 1
    worksheet.write(row, col, "Total")


# Writing the data into the worksheet
def write_data(data1, data2, data3, data4, data5, total_length, worksheet, workbook):
    KM_TO_MILES_RATIO = 0.62137
    data1 = data1 / 1000
    data2= data2 / 1000
    data3 = data3 / 1000
    data4 = data4 / 1000
    data5 = data5 / 1000
    
    # Set the column size.
    column_sizeB = worksheet.set_column('B:B', 20)
    column_sizeC = worksheet.set_column('C:C', 20)
    header_format = workbook.add_format()
    header_format.set_align ('center')
    header_format.set_bold()
    worksheet.set_row(0,None,header_format)
    worksheet.set_row(1,None,header_format)
    # Adds the percent sign and puts it in percent form.
    percent_format = workbook.add_format({'num_format': '0.00%'})
    percent = worksheet.set_column('D:D', 10, percent_format)
    # Formats to not show decimal places
    cell_format1 = workbook.add_format()
    cell_format1.set_num_format(0x01)
    cell_format1.set_align ('right')

    col = 1
    row = 2
    worksheet.write(row, col, data1, cell_format1)
    col += 1
    worksheet.write(row, col, data1 * KM_TO_MILES_RATIO, cell_format1)
    col += 1
    worksheet.write(row, col, data1 / total_length, percent)

    col = 1
    row = 3
    worksheet.write(row, col, data2, cell_format1)
    col += 1
    worksheet.write(row, col, data2 * KM_TO_MILES_RATIO, cell_format1)
    col += 1
    worksheet.write(row, col, data2 / total_length, percent)

    col = 1
    row = 4
    worksheet.write(row, col, data3, cell_format1)
    col += 1
    worksheet.write(row, col, data3 * KM_TO_MILES_RATIO, cell_format1)
    col += 1
    worksheet.write(row, col, data3 / total_length, percent)

    col = 1
    row = 5
    worksheet.write(row, col, data4, cell_format1)
    col += 1
    worksheet.write(row, col, data4 * KM_TO_MILES_RATIO, cell_format1)
    col += 1
    worksheet.write(row, col, data4 / total_length, percent)

    col = 1
    row = 6
    worksheet.write(row, col, data5, cell_format1)
    col += 1
    worksheet.write(row, col, data5 * KM_TO_MILES_RATIO, cell_format1)
    col += 1
    worksheet.write(row, col, data5 / total_length, percent)

    # Calculating Total for Stream Length(Km)
    worksheet.write(7, 1, '=SUM(B3:B7)', cell_format1)
    # Calculating Total for Stream Length (mi)
    worksheet.write(7, 2, '=SUM(C3:C7)', cell_format1)
    # Calculating total percentage.
    worksheet.write(7, 3, '=SUM(D3:D7)', percent)


# Getting the data for Complex Size
# loop through multiple streams
def search_cursor(fields, data1, data2, data3, data4, data5, total, stream_network, is_complex, is_capacity_total, worksheet, workbook):
    split_input = stream_network.split(";")
    if is_capacity_total:
        for streams in split_input:
            with arcpy.da.SearchCursor(streams, fields) as cursor:
                for capacity, dam_complex_size in cursor:
                    total += dam_complex_size
                    if capacity == 0:
                        data5 += dam_complex_size
                    elif capacity <= 1:
                        data4 += dam_complex_size
                    elif capacity <= 5:
                        data3 += dam_complex_size
                    elif capacity <= 15:
                        data2 += dam_complex_size
                    else:
                        data1 += dam_complex_size
        return data1, data2, data3, data4, data5, total

    elif is_complex:
        for streams in split_input:
            with arcpy.da.SearchCursor(streams, fields) as cursor:
                for length, dam_complex_size in cursor:
                    total += length
                    if dam_complex_size == 0:
                        data1 += length
                    elif dam_complex_size <= 1:
                        data2 += length
                    elif dam_complex_size <= 3:
                        data3 += length
                    elif dam_complex_size <= 5:
                        data4 += length
                    else:
                        data5 += length
        total = total/1000
        write_data(data1, data2, data3, data4, data5, total, worksheet, workbook)
    else:
        for streams in split_input:
            with arcpy.da.SearchCursor(streams, fields) as cursor:
                for length, ex_build_cap_size in cursor:
                    total += length
                    if ex_build_cap_size == 0:
                        data1 += length
                    elif ex_build_cap_size <= 1:
                        data2 += length
                    elif ex_build_cap_size <= 5:
                        data3 += length
                    elif ex_build_cap_size <= 15:
                        data4 += length
                    else:
                        data5 += length
        total = total/1000
        write_data(data1, data2, data3, data4, data5, total, worksheet, workbook)
        
def column_calc (minimum, watershed):
    if minimum > (len(watershed)+10):
        return minimum
    else:
        return (len(watershed)+10)

def write_summary_worksheet (worksheet, stream_network, watershed_name, workbook, fields_list):
    
    # formatting
    
    column_sizeA = worksheet.set_column('A:A', column_calc (32, watershed_name))
    column_sizeB = worksheet.set_column('B:B', 10)
    column_sizeC = worksheet.set_column('C:C', 5)
    column_sizeD = worksheet.set_column('D:D', 37)
    header_format = workbook.add_format()
    header_format.set_align ('center')
    header_format.set_bold()
    worksheet.set_row(0,None,header_format)
    worksheet.set_row(1,None,header_format)
    percent_format = workbook.add_format({'num_format': '0.00%'})
    percent1 = worksheet.set_column('E:E', 10, percent_format)
    color = workbook.add_format()
    color.set_bg_color ('C0C0C0')
    cell_format1 = workbook.add_format()
    cell_format1.set_num_format(0x01)
    cell_format1.set_align ('right') 
    
    
    # categories
    
    row = 0
    col = 0
    worksheet.write(row, col, watershed_name, column_sizeA)
    row += 2
    worksheet.write(row, col, "Total Stream Length (Km)")
    row += 1
    worksheet.write(row, col, "Total Stream Length (mi)")
    row += 1
    worksheet.write(row, col, "Total Existing Dam Complex Size")
    row += 1
    worksheet.write(row, col, "Total Historic Dam Complex Size")
    row += 1
    worksheet.write(row, col, "Total Existing Vegetation Capacity")
    row += 1
    worksheet.write(row, col, "Total Historic Vegetation Capacity")
    
    row = 2
    col = 3
    worksheet.write(row, col, "% Reaches Estimated Correctly")
    row += 1
    worksheet.write(row, col, "% Network \"Easiest - Low-Hanging Fruit\"")
    row += 1
    worksheet.write(row, col, "% Network \"Dam Building Possible\"")
    row += 1
    worksheet.write(row, col, "% Network \"Negligible Risk\"")
    
    split_input = stream_network.split(";")
    
    # total stream lengths

    totalStreamLengthKm = 0.0
    totalStreamLengthMi = 0.0
    fields = ['SHAPE@Length']
    for streams in split_input:
        with arcpy.da.SearchCursor(streams, fields) as cursor:
            for length, in cursor:
                totalStreamLengthKm += length

    totalStreamLengthKm /= 1000
    totalStreamLengthMi = totalStreamLengthKm * 1.609344
    

    # total complex sizes
    
    fields = ['SHAPE@Length', "mCC_EX_CT"]    
    if fields[1] in fields_list:
        totalExistingComplex = 0.0
        for streams in split_input:
                with arcpy.da.SearchCursor(streams, fields) as cursor:
                    for length, dam_complex_size in cursor:
                        totalExistingComplex += dam_complex_size
    else:
        arcpy.AddWarning("Could not complete summary worksheet: {0} not in fields.".format(fields[1]))
        totalExistingComplex = "N/A"

    
    fields = ['SHAPE@Length', "mCC_HPE_CT"]
    if fields[1] in fields_list:
        totalHistoricComplex = 0.0
        for streams in split_input:
                with arcpy.da.SearchCursor(streams, fields) as cursor:
                    for length, dam_complex_size in cursor:
                        totalHistoricComplex += dam_complex_size
    else:
        arcpy.AddWarning("Could not complete summary worksheet: {0} not in fields.".format(fields[1]))
        totalHistoricComplex = "N/A"

    # total vegetaion capacity

    fields = ['SHAPE@Length', "oVC_EX"]
    if fields[1] in fields_list:
        totalExistingVeg = 0.0
        for streams in split_input:
                with arcpy.da.SearchCursor(streams, fields) as cursor:
                    for length, density in cursor:
                        totalExistingVeg += ((length/1000)*density)
    else:
        arcpy.AddWarning("Could not complete summary worksheet: {0} not in fields.".format(fields[1]))
        totalExistingVeg = "N/A"
    
    fields = ['SHAPE@Length', "oVC_Hpe"]
    if fields[1] in fields_list:
        totalHistoricVeg = 0.0
        for streams in split_input:
                with arcpy.da.SearchCursor(streams, fields) as cursor:
                    for length, density in cursor:
                        totalHistoricVeg += ((length/1000)*density)
    else:
        arcpy.AddWarning("Could not complete summary worksheet: {0} not in fields.".format(fields[1]))
        totalHistoricVeg = "N/A"

    # percent estimated correctly

    estimateRight = 0
    estimateWrong =0

    fields = ['SHAPE@Length', 'BRATvSurv']
    if fields[1] in fields_list:
        percentCorrectEstimate = 0.0
        for streams in split_input:
                with arcpy.da.SearchCursor(streams, fields) as cursor:
                    for length, valid in cursor:
                        if valid >= 1:
                            estimateRight += 1
                        elif valid == -1:
                            estimateRight += 1
                        elif valid < 1:
                            estimateWrong += 1
                        else:
                            pass

        percentCorrectEstimate = float(estimateRight) / (float(estimateWrong) + float(estimateRight))
    else:
        arcpy.AddWarning("Could not complete summary worksheet: {0} not in fields.".format(fields[1]))
        percentCorrectEstimate = "N/A"

    

    # percent network "Easiest-Low Hanging Fruit"

    fields = ['SHAPE@Length', "oPBRC_CR"]
    easiestLength = 0.0
    if fields[1] in fields_list:
        percentEasiest = 0.0
        for streams in split_input:
                with arcpy.da.SearchCursor(streams, fields) as cursor:
                    for length, category in cursor:
                        if category=="Easiest - Low-Hanging Fruit":
                            easiestLength+=length
                        else:
                            pass
        percentEasiest = easiestLength/(totalStreamLengthKm*1000)
    else:
        arcpy.AddWarning("Could not complete summary worksheet: {0} not in fields.".format(fields[1]))
        percentEasiest = "N/A"
        
    # percent network "Dam Building Possible"
    
    fields = ['SHAPE@Length', "oPBRC_UD"]
    possibleLength = 0.0
    if fields[1] in fields_list:
        percentPossible = 0.0
        for streams in split_input:
                with arcpy.da.SearchCursor(streams, fields) as cursor:
                    for length, category in cursor:
                        if category=="Dam Building Possible":
                            possibleLength+=length
                        else:
                            pass
        percentPossible = possibleLength/(totalStreamLengthKm*1000)
    else:
        arcpy.AddWarning("Could not complete summary worksheet: {0} not in fields.".format(fields[1]))
        percentPossible = "N/A"
        
    # percent network "Negligible Risk"
    
    fields = ['SHAPE@Length', "oPBRC_UI"]
    negligibleLength = 0.0
    if fields[1] in fields_list:
        percentNegligible = 0.0
        for streams in split_input:
                with arcpy.da.SearchCursor(streams, fields) as cursor:
                    for length, category in cursor:
                        if category=="Negligible Risk":
                            negligibleLength+=length
                        else:
                            pass
                        
        percentNegligible = negligibleLength/(totalStreamLengthKm*1000)
    else:
        arcpy.AddWarning("Could not complete summary worksheet: {0} not in fields.".format(fields[1]))
        percentNegligible = "N/A"
        
    # output all calculations

    row = 2
    col = 1
    worksheet.write(row, col, totalStreamLengthKm, cell_format1)
    row += 1
    worksheet.write(row, col, totalStreamLengthMi, cell_format1)
    row += 1
    worksheet.write(row, col, totalExistingComplex, cell_format1)
    row += 1
    worksheet.write(row, col, totalHistoricComplex, cell_format1)
    row += 1
    worksheet.write(row, col, totalExistingVeg, cell_format1)
    row += 1
    worksheet.write(row, col, totalHistoricVeg, cell_format1)
    row = 2
    col = 4
    worksheet.write(row, col, percentCorrectEstimate, percent1)
    row += 1
    worksheet.write(row, col, percentEasiest, percent1)
    row += 1
    worksheet.write(row, col, percentPossible, percent1)
    row += 1
    worksheet.write(row, col, percentNegligible, percent1)
    


def write_exist_complex_worksheet(exist_complex_worksheet, stream_network, watershed_name, workbook):
    is_complex = True

    write_header(exist_complex_worksheet, watershed_name)
    write_categories_complex(exist_complex_worksheet, watershed_name)

    fields = ['SHAPE@Length', "mCC_EX_CT"]
    no_dams_length = 0.0
    one_dam_length = 0.0
    some_dams_length = 0.0
    more_dams_length = 0.0
    many_dams_length = 0.0
    total_length = 0.0

    exist_complex_worksheet.write(1, 0, fields[1])

    search_cursor(fields, no_dams_length, one_dam_length, some_dams_length, more_dams_length, many_dams_length, total_length, stream_network, is_complex, False, exist_complex_worksheet, workbook)


def write_exist_build_cap_worksheet(exist_build_cap_worksheet, stream_network, watershed_name, workbook):
    is_complex = False
    write_header(exist_build_cap_worksheet, watershed_name)

    write_categories_build_cap(exist_build_cap_worksheet, watershed_name)

    fields = ['SHAPE@Length', "oCC_EX"]
    none = 0.0
    rare = 0.0
    occasional = 0.0
    frequent = 0.0
    pervasive = 0.0
    total_length = 0.0

    exist_build_cap_worksheet.write(1, 0, fields[1])

    search_cursor(fields, none, rare, occasional, frequent, pervasive, total_length, stream_network, is_complex, False, exist_build_cap_worksheet, workbook)


def write_hist_complex_worksheet(hist_complex_worksheet, stream_network, watershed_name, workbook):
    is_complex = True
    write_header(hist_complex_worksheet, watershed_name)
    write_categories_complex(hist_complex_worksheet, watershed_name)

    fields = ['SHAPE@Length', "mCC_HPE_CT"]
    no_dams_length = 0.0
    one_dam_length = 0.0
    some_dams_length = 0.0
    more_dams_length = 0.0
    many_dams_length = 0.0
    total_length = 0.0

    hist_complex_worksheet.write(1, 0, fields[1])
    
    search_cursor(fields, no_dams_length, one_dam_length, some_dams_length, more_dams_length, many_dams_length, total_length, stream_network, is_complex, False, hist_complex_worksheet, workbook)


def write_hist_build_cap_worksheet(hist_build_cap_worksheet, stream_network, watershed_name, workbook):
    is_complex = False
    write_header(hist_build_cap_worksheet, watershed_name)
    write_categories_build_cap(hist_build_cap_worksheet, watershed_name)

    fields = ['SHAPE@Length', "oCC_HPE"]
    none = 0.0
    rare = 0.0
    occasional = 0.0
    frequent = 0.0
    pervasive = 0.0
    total_capacity = 0.0

    hist_build_cap_worksheet.write(1, 0, fields[1])

    search_cursor(fields, none, rare, occasional, frequent, pervasive, total_capacity, stream_network, is_complex, False, hist_build_cap_worksheet, workbook)


def write_hist_vs_exist_worksheet(hist_vs_exist_worksheet, stream_network, watershed_name, workbook):

    column_sizeA = hist_vs_exist_worksheet.set_column('A:A', column_calc (25, watershed_name))
    column_sizeB = hist_vs_exist_worksheet.set_column('B:B', 20)
    column_sizeC = hist_vs_exist_worksheet.set_column('C:C', 20)
    column_sizeD = hist_vs_exist_worksheet.set_column('D:D', 25)
    column_sizeE = hist_vs_exist_worksheet.set_column('E:E', 2)
    column_sizeF = hist_vs_exist_worksheet.set_column('F:F', 20)
    column_sizeG = hist_vs_exist_worksheet.set_column('G:G', 20)
    column_sizeH = hist_vs_exist_worksheet.set_column('H:H', 25)
    column_sizeI = hist_vs_exist_worksheet.set_column('I:I', 2)
    column_sizeJ = hist_vs_exist_worksheet.set_column('J:J', 20)
    column_sizeK = hist_vs_exist_worksheet.set_column('K:K', 5)
    column_sizeL = hist_vs_exist_worksheet.set_column('L:L', 30)
    column_sizeM = hist_vs_exist_worksheet.set_column('M:M', 30)
    column_sizeN = hist_vs_exist_worksheet.set_column('N:N', 5)
    column_sizeO = hist_vs_exist_worksheet.set_column('O:O', 15)
    header_format = workbook.add_format()
    header_format.set_align ('center')
    header_format.set_bold()
    hist_vs_exist_worksheet.set_row(0,None,header_format)
    hist_vs_exist_worksheet.set_row(1,None,header_format)
    hist_vs_exist_worksheet.set_row(2,None,header_format)
    percent_format = workbook.add_format({'num_format': '0.00%'})
    percent1 = hist_vs_exist_worksheet.set_column('C:C', 20, percent_format)
    percent2 = hist_vs_exist_worksheet.set_column('G:G', 20, percent_format)
    percent3 = hist_vs_exist_worksheet.set_column('O:O', 7, percent_format)
    percent4 = hist_vs_exist_worksheet.set_column('J:J', 20, percent_format)
    color = workbook.add_format()
    color.set_bg_color('#C0C0C0')
    hist_vs_exist_worksheet.write("A3", "", color)
    cell_format2 = workbook.add_format()
    cell_format2.set_num_format(0x02) 

    # Headers
    row = 0
    col = 0
    hist_vs_exist_worksheet.write(row, col, watershed_name, column_sizeA)
    row += 1
    col += 2
    hist_vs_exist_worksheet.write(row, col, "Existing Capacity")
    col += 4
    hist_vs_exist_worksheet.write(row, col, "Historic Capacity")
    row += 1
    col = 0
    hist_vs_exist_worksheet.write(row, col, "Category")
    col += 1
    hist_vs_exist_worksheet.write(row, col, "Stream Length (km)", column_sizeB)
    col += 1
    hist_vs_exist_worksheet.write(row, col, "% of Stream Network", column_sizeC)
    col += 1
    hist_vs_exist_worksheet.write(row, col, "Estimated Dam Capacity", column_sizeD)
    col += 1
    hist_vs_exist_worksheet.write(row, col, "", column_sizeE)
    col += 1
    hist_vs_exist_worksheet.write(row, col, "Stream Length (km)", column_sizeF)
    col += 1
    hist_vs_exist_worksheet.write(row, col, "% of Stream Network", column_sizeG)
    col += 1
    hist_vs_exist_worksheet.write(row, col, "Estimated Dam Capacity", column_sizeH)
    col += 1
    hist_vs_exist_worksheet.write(row, col, "", column_sizeI)
    col += 1
    hist_vs_exist_worksheet.write(row, col, "% Capacity of Historic", column_sizeJ)
    col += 1
    hist_vs_exist_worksheet.write(row, col, "", column_sizeK)
    col += 1
    row=2
    col=11
    hist_vs_exist_worksheet.write(row, col, "Estimated Existing Dams/km total", column_sizeL)
    col += 1
    hist_vs_exist_worksheet.write(row, col, "Estimated Historic Dams/km total", column_sizeM)
    col += 1
    hist_vs_exist_worksheet.write(row, col, "", column_sizeN)
    col += 1
    hist_vs_exist_worksheet.write(row, col, "%loss", column_sizeO)

    # Categories:
    write_categories_hist_vs_exist(hist_vs_exist_worksheet)

    # Existing - Stream Length: Starting at B4 - B8 get numbers from Existing Capacity, B7 - B3
    row = 3
    col = 1
    hist_vs_exist_worksheet.write(row, col, "=INT('Existing Dam Building Capacity'!B7)")
    row += 1
    hist_vs_exist_worksheet.write(row, col, "=INT('Existing Dam Building Capacity'!B6)")
    row += 1
    hist_vs_exist_worksheet.write(row, col, "=INT('Existing Dam Building Capacity'!B5)")
    row += 1
    hist_vs_exist_worksheet.write(row, col, "=INT('Existing Dam Building Capacity'!B4)")
    row += 1
    hist_vs_exist_worksheet.write(row, col, "=INT('Existing Dam Building Capacity'!B3)")
    row += 1
    hist_vs_exist_worksheet.write(row, col, '=SUM(B4:B8)')

    # Existing - % of Stream Network
    row = 3
    col = 2
    hist_vs_exist_worksheet.write(row, col, '=(B4/$B$9)', percent1)
    row += 1
    hist_vs_exist_worksheet.write(row, col, '=(B5/$B$9)', percent1)
    row += 1
    hist_vs_exist_worksheet.write(row, col, '=(B6/$B$9)', percent1)
    row += 1
    hist_vs_exist_worksheet.write(row, col, '=(B7/$B$9)', percent1)
    row += 1
    hist_vs_exist_worksheet.write(row, col, '=(B8/$B$9)', percent1)
    row += 1
    hist_vs_exist_worksheet.write(row, col, '=SUM(C4:C8)', percent1)

    # Existing - estimated dam capacity
    fields = ["oCC_EX", "mCC_EX_CT"]
    none = 0.0
    rare = 0.0
    occasional = 0.0
    frequent = 0.0
    pervasive = 0.0
    total_capacity = 0.0
    pervasive, frequent, occasional, rare, none, total = search_cursor(fields, pervasive, frequent, occasional, rare, none, total_capacity, stream_network, False, True, hist_vs_exist_worksheet, workbook)
    row = 3
    col = 3
    hist_vs_exist_worksheet.write(row, col, int(pervasive))
    row += 1
    hist_vs_exist_worksheet.write(row, col, int(frequent))
    row += 1
    hist_vs_exist_worksheet.write(row, col, int(occasional))
    row += 1
    hist_vs_exist_worksheet.write(row, col, int(rare))
    row += 1
    hist_vs_exist_worksheet.write(row, col, int(none))
    row += 1
    hist_vs_exist_worksheet.write(row, col, "=SUM(D4:D8)")
                                  
    # Historic - Stream Length: Starting at B4 - B8 get numbers from Existing Capacity, B7 - B3
    row = 3
    col = 5
    hist_vs_exist_worksheet.write(row, col, "=INT('Historic Dam Building Capacity'!B7)")
    row += 1
    hist_vs_exist_worksheet.write(row, col, "=INT('Historic Dam Building Capacity'!B6)")
    row += 1
    hist_vs_exist_worksheet.write(row, col, "=INT('Historic Dam Building Capacity'!B5)")
    row += 1
    hist_vs_exist_worksheet.write(row, col, "=INT('Historic Dam Building Capacity'!B4)")
    row += 1
    hist_vs_exist_worksheet.write(row, col, "=INT('Historic Dam Building Capacity'!B3)")
    row += 1
    hist_vs_exist_worksheet.write(row, col, '=SUM(F4:F8)')

    # Historic - % of Stream Network
    row = 3
    col = 6
    hist_vs_exist_worksheet.write(row, col, '=(F4/$F$9)', percent2)
    row += 1
    hist_vs_exist_worksheet.write(row, col, '=(F5/$F$9)', percent2)
    row += 1
    hist_vs_exist_worksheet.write(row, col, '=(F6/$F$9)', percent2)
    row += 1
    hist_vs_exist_worksheet.write(row, col, '=(F7/$F$9)', percent2)
    row += 1
    hist_vs_exist_worksheet.write(row, col, '=(F8/$F$9)', percent2)
    row += 1
    hist_vs_exist_worksheet.write(row, col, '=SUM(G4:G8)', percent2)

    # Historic - estimated dam capacity
    fields = ["oCC_HPE", "mCC_HPE_CT"]
    none = 0.0
    rare = 0.0
    occasional = 0.0
    frequent = 0.0
    pervasive = 0.0
    total_capacity = 0.0
    pervasive, frequent, occasional, rare, none, total = search_cursor(fields, pervasive, frequent, occasional, rare, none, total_capacity, stream_network, False, True, hist_vs_exist_worksheet, workbook)
    row = 3
    col = 7
    hist_vs_exist_worksheet.write(row, col, int(pervasive))
    row += 1
    hist_vs_exist_worksheet.write(row, col, int(frequent))
    row += 1
    hist_vs_exist_worksheet.write(row, col, int(occasional))
    row += 1
    hist_vs_exist_worksheet.write(row, col, int(rare))
    row += 1
    hist_vs_exist_worksheet.write(row, col, int(none))
    row += 1
    hist_vs_exist_worksheet.write(row, col, "=SUM(H4:H8)")


    # % Capacity of Historic
    row = 3
    col = 9
    # Checking if the cell to the left equals zero. This is to prevent div by zero errors
    if int(pervasive)== 0:
        hist_vs_exist_worksheet.write(row, col, 0, percent1)
    else:
        hist_vs_exist_worksheet.write(row, col, '=(D4/H4)', percent4)
    row += 1
    if int(frequent)== 0:
        hist_vs_exist_worksheet.write(row, col, 0, percent1)
    else:
        hist_vs_exist_worksheet.write(row, col, '=(D5/H5)', percent4)
    row += 1
    if int(occasional)== 0:
        hist_vs_exist_worksheet.write(row, col, 0)
    else:
        hist_vs_exist_worksheet.write(row, col, '=(D6/H6)', percent4)
    row += 1
    if int(rare)== 0:
        hist_vs_exist_worksheet.write(row, col, 0)
    else:
        hist_vs_exist_worksheet.write(row, col, '=(D7/H7)', percent4)
    row += 1
    if int(none)== 0:
        hist_vs_exist_worksheet.write(row, col, 0)
    else:
        hist_vs_exist_worksheet.write(row, col, '=(D8/H8)', percent4)
    row += 1
    hist_vs_exist_worksheet.write(row, col, '=(D9/H9)', percent1)

    # totals
    hist_vs_exist_worksheet.write(3, 11, '=(D9/B9)', cell_format2)
    hist_vs_exist_worksheet.write(3, 12, '=(H9/F9)', cell_format2)
    hist_vs_exist_worksheet.write(3, 14, '=1-$J$9', percent3)


def write_conservation_restoration(worksheet, stream_network, watershed_name, workbook):

    column_sizeA = worksheet.set_column('A:A', column_calc (30, watershed_name))
    column_sizeB = worksheet.set_column('B:B', 20)
    column_sizeC = worksheet.set_column('C:C', 20)
    column_sizeD = worksheet.set_column('D:D', 15)
    header_format = workbook.add_format()
    header_format.set_align ('center')
    header_format.set_bold()
    worksheet.set_row(0,None,header_format)
    worksheet.set_row(1,None,header_format)
    percent_format = workbook.add_format({'num_format': '0.00%'})
    percent = worksheet.set_column('D:D', 10, percent_format)
    color = workbook.add_format()
    color.set_bg_color('#C0C0C0')
    cell_format1 = workbook.add_format()
    cell_format1.set_num_format(0x01)
    cell_format1.set_align ('right')
    cell_format1.set_align ('right')


    # headers
    row = 0
    col = 0
    worksheet.write(row, col, watershed_name, column_sizeA)
    row += 1
    worksheet.write(row, col, "oPBRC_CR")
    col += 1
    worksheet.write(row, col, "Stream Length (km)", column_sizeB)
    col += 1
    worksheet.write(row, col, "Stream Length (mi)", column_sizeC)
    col += 1
    worksheet.write(row, col, "Percent", column_sizeD)

    # categories
    row = 2
    col = 0
    worksheet.write(row, col, "Easiest - Low-Hanging Fruit")
    row += 1
    worksheet.write(row, col, "Straight Forward - Quick Return")
    row += 1
    worksheet.write(row, col, "Strategic - Long-Term Investment")
    row += 1
    worksheet.write(row, col, "Other")
    row += 1
    worksheet.write(row, col, "Total")

    # calculate fields
    easy = 0
    mod = 0
    strateg = 0
    other = 0
    total = 0
    split_input = stream_network.split(";")
    for streams in split_input:
        with arcpy.da.SearchCursor(streams, ['SHAPE@Length', 'oPBRC_CR']) as cursor:
            for length, category in cursor:
                total += length
                if category == "Easiest - Low-Hanging Fruit":
                    easy += length
                elif category == "Straight Forward - Quick Return":
                    mod += length
                elif category == "Strategic - Long-Term Investment":
                    strateg += length
                else:
                    other += length
    # convert from m to km
    easy /= 1000
    mod /= 1000
    strateg /= 1000
    other /= 1000
    
    # write fields
    row = 2
    col = 1
    worksheet.write(row, col, easy, cell_format1)
    row += 1
    worksheet.write(row, col, mod, cell_format1)
    row += 1
    worksheet.write(row, col, strateg, cell_format1)
    row += 1
    worksheet.write(row, col, other, cell_format1)
    row += 1
    worksheet.write(row, col, "=SUM(B3:B6)", cell_format1)

    # calculate km to mi
    col += 1
    row = 2
    worksheet.write(row, col, "=B3*0.62137", cell_format1)
    row += 1
    worksheet.write(row, col, "=B4*0.62137", cell_format1)
    row += 1
    worksheet.write(row, col, "=B5*0.62137", cell_format1)
    row += 1
    worksheet.write(row, col, "=B6*0.62137", cell_format1)
    row += 1
    worksheet.write(row, col, "=SUM(C3:C6)", cell_format1)

    # calculate percents
    col += 1
    row = 2
    worksheet.write(row, col, '=B3/B7', percent)
    row += 1
    worksheet.write(row, col, '=B4/B7', percent)
    row += 1
    worksheet.write(row, col, '=B5/B7', percent)
    row += 1
    worksheet.write(row, col, '=B6/B7', percent)
    row += 1
    worksheet.write(row, col, '=B7/B7', percent)



def write_unsuitable_worksheet(worksheet, stream_network, watershed_name, workbook):
    
    column_sizeA = worksheet.set_column('A:A', column_calc (36, watershed_name))
    column_sizeB = worksheet.set_column('B:B', 20)
    column_sizeC = worksheet.set_column('C:C', 20)
    column_sizeD = worksheet.set_column('D:D', 15)
    header_format = workbook.add_format()
    header_format.set_align ('center')
    header_format.set_bold()
    worksheet.set_row(0,None,header_format)
    worksheet.set_row(1,None,header_format)
    percent_format = workbook.add_format({'num_format': '0.00%'})
    percent = worksheet.set_column('D:D', 10, percent_format)
    color = workbook.add_format()
    color.set_bg_color('#C0C0C0')
    cell_format1 = workbook.add_format()
    cell_format1.set_num_format(0x01)
    cell_format1.set_align ('right') 

    # headers
    row = 0
    col = 0
    worksheet.write(row, col, watershed_name, column_sizeA)
    row += 1
    worksheet.write(row, col, "oPBRC_UD")
    col += 1
    worksheet.write(row, col, "Stream Length (km)", column_sizeB)
    col += 1
    worksheet.write(row, col, "Stream Length (mi)", column_sizeC)
    col += 1
    worksheet.write(row, col, "Percent", column_sizeD)

    # categories
    row = 2
    col = 0
    worksheet.write(row, col, "Anthropogenicallly Limited")
    row += 1
    worksheet.write(row, col, "Naturally Vegetation Limited")
    row += 1
    worksheet.write(row, col, "Slope Limited")
    row += 1
    worksheet.write(row, col, "Stream Power Limited")
    row += 1
    worksheet.write(row, col, "Potential Reservoir or Landuse Change")
    row += 1
    worksheet.write(row, col, "Dam Building Possible")
    row += 1
    worksheet.write(row, col, "Stream Size Limited")
    row += 1
    worksheet.write(row, col, "Total")

    # calculate fields
    anth = 0
    veg = 0
    slope = 0
    stream = 0
    reservoir = 0
    dams = 0
    tbd = 0
    total = 0
    split_input = stream_network.split(";")
    for streams in split_input:
        with arcpy.da.SearchCursor(streams, ['SHAPE@Length', 'oPBRC_UD']) as cursor:
            for length, category in cursor:
                total += length
                if category == "Anthropogenically Limited":
                    anth += length
                elif category == "Naturally Vegetation Limited":
                    veg += length
                elif category == "Slope Limited":
                    slope += length
                elif category == "Stream Power Limited":
                    stream += length
                elif category == "Potential Reservoir or Landuse Change":
                    reservoir += length
                elif category == "Dam Building Possible":
                    dams += length
                elif category == "...TBD...":
                    tbd += length
                else:
                    pass
    # convert m to km
    anth /= 1000
    veg /= 1000
    slope /= 1000
    stream /= 1000
    reservoir /= 1000
    dams /= 1000
    tbd /= 1000
    
    row = 2
    col = 1
    worksheet.write(row, col, anth, cell_format1)
    row += 1
    worksheet.write(row, col, veg, cell_format1)
    row += 1
    worksheet.write(row, col, slope, cell_format1)
    row += 1
    worksheet.write(row, col, stream, cell_format1)
    row += 1
    worksheet.write(row, col, reservoir, cell_format1)
    row += 1
    worksheet.write(row, col, dams, cell_format1)
    row += 1
    worksheet.write(row, col, tbd, cell_format1)
    row += 1
    worksheet.write(row, col, "=SUM(B3:B9)", cell_format1)

    # calculate km to mi
    col += 1
    row = 2
    worksheet.write(row, col, "=B3*0.62137", cell_format1)
    row += 1
    worksheet.write(row, col, "=B4*0.62137", cell_format1)
    row += 1
    worksheet.write(row, col, "=B5*0.62137", cell_format1)
    row += 1
    worksheet.write(row, col, "=B6*0.62137", cell_format1)
    row += 1
    worksheet.write(row, col, "=B7*0.62137", cell_format1)
    row += 1
    worksheet.write(row, col, "=B8*0.62137", cell_format1)
    row += 1
    worksheet.write(row, col, "=B9*0.62137", cell_format1)
    row += 1
    worksheet.write(row, col, "=SUM(C3:C9)", cell_format1)

    # calculate percents
    col += 1
    row = 2
    worksheet.write(row, col, '=B3/B10', percent)
    row += 1
    worksheet.write(row, col, '=B4/B10', percent)
    row += 1
    worksheet.write(row, col, '=B5/B10', percent)
    row += 1
    worksheet.write(row, col, '=B6/B10', percent)
    row += 1
    worksheet.write(row, col, '=B7/B10', percent)
    row += 1
    worksheet.write(row, col, '=B8/B10', percent)
    row += 1
    worksheet.write(row, col, '=B9/B10', percent)
    row += 1
    worksheet.write(row, col, '=B10/B10', percent)


def write_risk_worksheet(worksheet, stream_network, watershed_name, workbook):
    
    column_sizeA = worksheet.set_column('A:A', column_calc (25, watershed_name))
    column_sizeB = worksheet.set_column('B:B', 20)
    column_sizeC = worksheet.set_column('C:C', 20)
    column_sizeD = worksheet.set_column('D:D', 15)
    header_format = workbook.add_format()
    header_format.set_align ('center')
    header_format.set_bold()
    worksheet.set_row(0,None,header_format)
    worksheet.set_row(1,None,header_format)
    percent_format = workbook.add_format({'num_format': '0.00%'})
    percent = worksheet.set_column('D:D', 10, percent_format)
    color = workbook.add_format()
    color.set_bg_color('#C0C0C0')
    cell_format1 = workbook.add_format()
    cell_format1.set_num_format(0x01)
    cell_format1.set_align ('right') 


    # headers
    row = 0
    col = 0
    worksheet.write(row, col, watershed_name, column_sizeA)
    row += 1
    worksheet.write(row, col, "oPBRC_UI")
    col += 1
    worksheet.write(row, col, "Stream Length (km)", column_sizeB)
    col += 1
    worksheet.write(row, col, "Stream Length (mi)", column_sizeC)
    col += 1
    worksheet.write(row, col, "Percent", column_sizeD)

    # categories
    row = 2
    col = 0
    worksheet.write(row, col, "Considerable Risk")
    row += 1
    worksheet.write(row, col, "Some Risk")
    row += 1
    worksheet.write(row, col, "Minor Risk")
    row += 1
    worksheet.write(row, col, "Negligible Risk")
    row += 1
    worksheet.write(row, col, "Total")

    # calculate fields
    cons = 0
    some = 0
    minr = 0
    negl = 0
    total = 0
    split_input = stream_network.split(";")
    for streams in split_input:
        with arcpy.da.SearchCursor(streams, ['SHAPE@Length', 'oPBRC_UI']) as cursor:
            for length, category in cursor:
                total += length
                if category == "Considerable Risk":
                    cons += length
                elif category == "Some Risk":
                    some += length
                elif category == "Minor Risk":
                    minr += length
                elif category == "Negligible Risk":
                    negl += length
                else:
                    pass
    # convert m to km
    cons /= 1000
    some /= 1000
    minr /= 1000
    negl /= 1000

    # write values
    row = 2
    col = 1
    worksheet.write(row, col, cons, cell_format1)
    row += 1
    worksheet.write(row, col, some, cell_format1)
    row += 1
    worksheet.write(row, col, minr, cell_format1)
    row += 1
    worksheet.write(row, col, negl, cell_format1)
    row += 1
    worksheet.write(row, col, "=SUM(B3:B6)", cell_format1)

    # calculate km to mi
    col += 1
    row = 2
    worksheet.write(row, col, "=B3*0.62137", cell_format1)
    row += 1
    worksheet.write(row, col, "=B4*0.62137", cell_format1)
    row += 1
    worksheet.write(row, col, "=B5*0.62137", cell_format1)
    row += 1
    worksheet.write(row, col, "=B6*0.62137", cell_format1)
    row += 1
    worksheet.write(row, col, "=SUM(C3:C6)", cell_format1)

    # calculate percents
    col += 1
    row = 2
    worksheet.write(row, col, '=B3/B7', percent)
    row += 1
    worksheet.write(row, col, '=B4/B7', percent)
    row += 1
    worksheet.write(row, col, '=B5/B7', percent)
    row += 1
    worksheet.write(row, col, '=B6/B7', percent)
    row += 1
    worksheet.write(row, col, '=B7/B7', percent)


def write_strategies_worksheet(worksheet, stream_network, watershed_name, workbook):
    column_sizeA = worksheet.set_column('A:A', column_calc (25, watershed_name))
    column_sizeB = worksheet.set_column('B:B', 20)
    column_sizeC = worksheet.set_column('C:C', 20)
    column_sizeD = worksheet.set_column('D:D', 15)
    header_format = workbook.add_format()
    header_format.set_align ('center')
    header_format.set_bold()
    worksheet.set_row(0,None,header_format)
    worksheet.set_row(1,None,header_format)
    percent_format = workbook.add_format({'num_format': '0.00%'})
    percent = worksheet.set_column('D:D', 10, percent_format)
    color = workbook.add_format()
    color.set_bg_color('#C0C0C0')
    cell_format1 = workbook.add_format()
    cell_format1.set_num_format(0x01)
    cell_format1.set_align ('right') 

    # headers
    row = 0
    col = 0
    worksheet.write(row, col, watershed_name, column_sizeA)
    row += 1
    worksheet.write(row, col, "ConsVRest")
    col += 1
    worksheet.write(row, col, "Stream Length (km)", column_sizeB)
    col += 1
    worksheet.write(row, col, "Stream Length (mi)", column_sizeC)
    col += 1
    worksheet.write(row, col, "Percent", column_sizeD)

    # categories
    row = 2
    col = 0
    worksheet.write(row, col, "Immediate - Beaver Conservation")
    row += 1
    worksheet.write(row, col, "Immediate - Beaver Translocation")
    row += 1
    worksheet.write(row, col, "Mid Term - Riparian Vegetation Restoration")
    row += 1
    worksheet.write(row, col, "Long Term - Riparian Vegetation Reestablishment")
    row += 1
    worksheet.write(row, col, "Low Capacity Habitat")
    row += 1
    worksheet.write(row, col, "Total")

    # calculate fields
    cons = 0
    trns = 0
    rest = 0
    veg = 0
    low = 0
    total = 0
    split_input = stream_network.split(";")
    for streams in split_input:
        with arcpy.da.SearchCursor(streams, ['SHAPE@Length', 'ConsVRest']) as cursor:
            for length, category in cursor:
                total += length
                if category == "Immediate - Beaver Conservation":
                    cons += length
                elif category == "Immediate - Potential Beaver Translocation":
                    trns += length
                elif category == "Mid Term - Process-based Riparian Vegetation Restoration":
                    rest += length
                elif category == "Long Term - Riparian Vegetation Reestablishment":
                    veg += length
                elif category == "Low Capacity Habitat":
                    low += length
                else:
                    pass
    #convert m to km
    cons /= 1000
    trns /= 1000
    rest /= 1000
    veg /= 1000
    low /= 1000

    # write length km
    
    row = 2
    col = 1
    worksheet.write(row, col, cons, cell_format1)
    row += 1
    worksheet.write(row, col, trns, cell_format1)
    row += 1
    worksheet.write(row, col, rest, cell_format1)
    row += 1
    worksheet.write(row, col, veg, cell_format1)
    row += 1
    worksheet.write(row, col, low, cell_format1)
    row += 1
    worksheet.write(row, col, "=SUM(B3:B7)", cell_format1)

    # calculate km to mi
    col += 1
    row = 2
    worksheet.write(row, col, "=B3*0.62137", cell_format1)
    row += 1
    worksheet.write(row, col, "=B4*0.62137", cell_format1)
    row += 1
    worksheet.write(row, col, "=B5*0.62137", cell_format1)
    row += 1
    worksheet.write(row, col, "=B6*0.62137", cell_format1)
    row += 1
    worksheet.write(row, col, "=B7*0.62137", cell_format1)
    row += 1
    worksheet.write(row, col, "=SUM(C3:C7)", cell_format1)

    # calculate percents
    col += 1
    row = 2
    worksheet.write(row, col, '=B3/B8', percent)
    row += 1
    worksheet.write(row, col, '=B4/B8', percent)
    row += 1
    worksheet.write(row, col, '=B5/B8', percent)
    row += 1
    worksheet.write(row, col, '=B6/B8', percent)
    row += 1
    worksheet.write(row, col, '=B7/B8', percent)
    row += 1
    worksheet.write(row, col, '=B8/B8', percent)


def write_validation_worksheet(worksheet, stream_network, watershed_name, workbook):
    column_sizeA = worksheet.set_column('A:A', column_calc (40, watershed_name))
    column_sizeB = worksheet.set_column('B:B', 18)
    column_sizeC = worksheet.set_column('C:C', 15)
    column_sizeD = worksheet.set_column('D:D', 20)
    column_sizeE = worksheet.set_column('E:E', 20)
    column_sizeF = worksheet.set_column('F:F', 15)
    header_format = workbook.add_format()
    header_format.set_align ('center')
    header_format.set_bold()
    worksheet.set_row(0,None,header_format)
    worksheet.set_row(1,None,header_format)
    percent_format = workbook.add_format({'num_format': '0.00%'})
    percent = worksheet.set_column('C:C', 20, percent_format)
    percent2 = worksheet.set_column('F:F', 15, percent_format)
    color = workbook.add_format()
    color.set_bg_color('#C0C0C0')
    cell_format1 = workbook.add_format()
    cell_format1.set_num_format(0x01)
    cell_format1.set_align ('right')

    # headers
    row = 0
    col = 0
    worksheet.write(row, col, watershed_name, column_sizeA)
    row += 1
    worksheet.write(row, col, "BRATvSurv")
    col += 1
    worksheet.write(row, col, "Number of Reaches", column_sizeB)
    col += 1
    worksheet.write(row, col, "Percent of Reaches", column_sizeC)
    col += 1
    worksheet.write(row, col, "Stream Length (km)", column_sizeD)
    col += 1
    worksheet.write(row, col, "Stream Length (mi)", column_sizeE)
    col += 1
    worksheet.write(row, col, "Percent Length", column_sizeF)

    # categories
    row = 2
    col = 0
    worksheet.write(row, col, "Fewer dams than predicted existing capacity")
    row += 1
    worksheet.write(row, col, "More dams than predicted existing capacity")
    row += 1
    worksheet.write(row, col, "No surveyed dams")
    row += 1
    worksheet.write(row, col, "Total")

    # calculate fields
    few_km = 0
    few = 0
    more_km = 0
    more = 0
    none_km = 0
    none = 0
    total_km = 0
    total = 0
    split_input = stream_network.split(";")
    for streams in split_input:
        with arcpy.da.SearchCursor(streams, ['SHAPE@Length', 'BRATvSurv']) as cursor:
            for length, valid in cursor:
                total_km += length
                total += 1
                if valid == -1:
                    none_km += length
                    none += 1
                elif valid >= 1:
                    few_km += length
                    few += 1
                elif valid < 1:
                    more_km += length
                    more += 1
                else:
                    pass

    few_km /= 1000
    more_km /= 1000
    none_km /= 1000
    total_km /= 1000
    # raw number of reaches
    row = 2
    col = 1
    worksheet.write(row, col, few)
    row += 1
    worksheet.write(row, col, more)
    row += 1
    worksheet.write(row, col, none)
    row += 1
    worksheet.write(row, col, "=SUM(B3:B5)")

    # percent of reaches
    row = 2
    col += 1
    worksheet.write(row, col, "=B3/B6", percent)
    row += 1
    worksheet.write(row, col, "=B4/B6", percent)
    row += 1
    worksheet.write(row, col, "=B5/B6", percent)
    row += 1
    worksheet.write(row, col, "=SUM(C3:C5)", percent)

    # length per category
    row = 2
    col += 1
    worksheet.write(row, col, few_km, cell_format1)
    row += 1
    worksheet.write(row, col, more_km, cell_format1)
    row += 1
    worksheet.write(row, col, none_km, cell_format1)
    row += 1
    worksheet.write(row, col, "=SUM(D3:D5)", cell_format1)
    
    # calculate km to mi
    col += 1
    row = 2
    worksheet.write(row, col, "=D3*0.62137", cell_format1)
    row += 1
    worksheet.write(row, col, "=D4*0.62137", cell_format1)
    row += 1
    worksheet.write(row, col, "=D5*0.62137", cell_format1)
    row += 1
    worksheet.write(row, col, "=SUM(E3:E5)", cell_format1)

    # calculate percents
    col += 1
    row = 2
    worksheet.write(row, col, '=D3/D6', percent2)
    row += 1
    worksheet.write(row, col, '=D4/D6', percent2)
    row += 1
    worksheet.write(row, col, '=D5/D6', percent2)
    row += 1
    worksheet.write(row, col, '=D6/D6', percent2)

def write_electivity_worksheet(worksheet, stream_network, watershed_name, workbook):

    # Formatting

    worksheet.set_column('A:A', column_calc (20, watershed_name))
    worksheet.set_column('B:B', 20)
    worksheet.set_column('C:C', 20)
    worksheet.set_column('D:D', 20)
    worksheet.set_column('E:E', 22)
    worksheet.set_column('F:F', 20)
    worksheet.set_column('G:G', 35)
    worksheet.set_column('H:H', 42)
    worksheet.set_column('I:I', 42)
    worksheet.set_column('J:J', 30)
    worksheet.set_column('K:K', 15)
    header_format = workbook.add_format()
    header_format.set_align ('center')
    header_format.set_bold()
    worksheet.set_row(0,None,header_format)
    worksheet.set_row(1,None,header_format)
    percent_format = workbook.add_format({'num_format': '0.00%'})
    percent_format.set_align ('right')
    percent1 = worksheet.set_column('E:E', 22, percent_format)
    percent2 = worksheet.set_column('J:J', 20, percent_format)
    color = workbook.add_format()
    color.set_bg_color ('C0C0C0')
    cell_format1 = workbook.add_format()
    cell_format1.set_num_format(0x01)
    cell_format1.set_align ('right')
    cell_format2 = workbook.add_format()
    cell_format2.set_num_format('0.0000')
    cell_format2.set_align ('right')

    # Create Column Labels
    row = 0
    col = 0
    worksheet.write(row, col, watershed_name)
    row += 1
    worksheet.write(row, col, "Segment Type")
    col += 1
    worksheet.write(row, col, "Stream Length (m)")
    col += 1
    worksheet.write(row, col, "Stream Length (Km)")
    col += 1
    worksheet.write(row, col, "Stream Length (mi)")
    col += 1
    worksheet.write(row, col, "% of Drainage Network")
    col += 1
    worksheet.write(row, col, "Surveyed Dams Count")
    col += 1
    worksheet.write(row, col, "BRAT Estimated Capacity Dam Count")
    col += 1
    worksheet.write(row, col, "Average Surveyed Dam Density (Dams/Km)")
    col += 1
    worksheet.write(row, col, "Average BRAT Predicted Density (Dams/Km)")
    col += 1
    worksheet.write(row, col, "% Modeled Capacity")
    col += 1
    worksheet.write(row, col, "Electivity Index")

    # Create Row Labels
    row = 2
    col = 0
    worksheet.write(row, col, "None")
    row += 1
    worksheet.write(row, col, "Rare")
    row += 1
    worksheet.write(row, col, "Occasional")
    row += 1
    worksheet.write(row, col, "Frequent")
    row += 1
    worksheet.write(row, col, "Pervasive")
    row += 1
    worksheet.write(row, col, "Total")
    row += 1

    # Column B (Stream Length Meters) 
    row = 2
    col = 1
    worksheet.write(row, col, "=C3*1000", cell_format1)
    row += 1
    worksheet.write(row, col, "=C4*1000", cell_format1)
    row += 1
    worksheet.write(row, col, "=C5*1000", cell_format1)
    row += 1
    worksheet.write(row, col, "=C6*1000", cell_format1)
    row += 1
    worksheet.write(row, col, "=C7*1000", cell_format1)
    row += 1
    worksheet.write(row, col, "=C8*1000", cell_format1)

    # Column C (Stream Length Kilometers) These values have already been calculated, so I'm just pulling them from the other Worksheet

    row = 2
    col = 2
    worksheet.write(row, col, "='Existing Dam Building Capacity'!B3", cell_format1)
    row += 1
    worksheet.write(row, col, "='Existing Dam Building Capacity'!B4", cell_format1)
    row += 1
    worksheet.write(row, col, "='Existing Dam Building Capacity'!B5", cell_format1)
    row += 1
    worksheet.write(row, col, "='Existing Dam Building Capacity'!B6", cell_format1)
    row += 1
    worksheet.write(row, col, "='Existing Dam Building Capacity'!B7", cell_format1)
    row += 1
    worksheet.write(row, col, "=='Existing Dam Building Capacity'!B8", cell_format1)

    # Column D (Stream Length Miles) These values have already been calculated, so I'm just pulling them from the other Worksheet

    row = 2
    col = 3
    worksheet.write(row, col, "='Existing Dam Building Capacity'!C3", cell_format1)
    row += 1
    worksheet.write(row, col, "='Existing Dam Building Capacity'!C4", cell_format1)
    row += 1
    worksheet.write(row, col, "='Existing Dam Building Capacity'!C5", cell_format1)
    row += 1
    worksheet.write(row, col, "='Existing Dam Building Capacity'!C6", cell_format1)
    row += 1
    worksheet.write(row, col, "='Existing Dam Building Capacity'!C7", cell_format1)
    row += 1
    worksheet.write(row, col, "=='Existing Dam Building Capacity'!C8", cell_format1)
    
    # Column E (Percent of Drainage Network) These values have already been calculated, so I'm just pulling them from the other Worksheet

    row = 2
    col = 4
    worksheet.write(row, col, "='Existing Dam Building Capacity'!D3", percent1)
    row += 1
    worksheet.write(row, col, "='Existing Dam Building Capacity'!D4", percent1)
    row += 1
    worksheet.write(row, col, "='Existing Dam Building Capacity'!D5", percent1)
    row += 1
    worksheet.write(row, col, "='Existing Dam Building Capacity'!D6", percent1)
    row += 1
    worksheet.write(row, col, "='Existing Dam Building Capacity'!D7", percent1)
    row += 1
    worksheet.write(row, col, "N/A", cell_format1)

    #Column F (Number of Surveyed Dams)

    none = 0.0
    rare = 0.0
    occ = 0.0
    freq = 0.0
    per = 0.0
    
    split_input = stream_network.split(";")
    fields = ['oCC_EX', "e_DamCt"]
    for streams in split_input:
        with arcpy.da.SearchCursor(streams, fields) as cursor:
            for capacity, dam_complex_size in cursor:
                if capacity == 0:
                    none += float(dam_complex_size)
                elif capacity <= 1:
                    rare += float(dam_complex_size)
                elif capacity <= 5:
                    occ += float(dam_complex_size)
                elif capacity <= 15:
                    freq += float(dam_complex_size)
                else:
                    per += float(dam_complex_size)
    row = 2
    col = 5
    worksheet.write(row, col, none, cell_format1)
    row += 1
    worksheet.write(row, col, rare, cell_format1)
    row += 1
    worksheet.write(row, col, occ, cell_format1)
    row += 1
    worksheet.write(row, col, freq, cell_format1)
    row += 1
    worksheet.write(row, col, per, cell_format1)
    row += 1
    worksheet.write(row, col, "=SUM(F3:F7)", cell_format1)

    # Column G (BRAT estimated Capacity)

    none = 0.0
    rare = 0.0
    occ = 0.0
    freq = 0.0
    per = 0.0
    
    split_input = stream_network.split(";")
    fields = ['oCC_EX', "mCC_EX_CT"]
    for streams in split_input:
        with arcpy.da.SearchCursor(streams, fields) as cursor:
            for capacity, dam_complex_size in cursor:
                if capacity == 0:
                    none += float(dam_complex_size)
                elif capacity <= 1:
                    rare += float(dam_complex_size)
                elif capacity <= 5:
                    occ += float(dam_complex_size)
                elif capacity <= 15:
                    freq += float(dam_complex_size)
                else:
                    per += float(dam_complex_size)
    row = 2
    col = 6
    worksheet.write(row, col, none, cell_format1)
    row += 1
    worksheet.write(row, col, rare, cell_format1)
    row += 1
    worksheet.write(row, col, occ, cell_format1)
    row += 1
    worksheet.write(row, col, freq, cell_format1)
    row += 1
    worksheet.write(row, col, per, cell_format1)
    row += 1
    worksheet.write(row, col, "=SUM(G3:G7)", cell_format1)

    # Column H (Average Surveyed Dam Density)

    row = 2
    col = 7
    worksheet.write(row, col, "=F3/C3", cell_format2)
    row += 1
    worksheet.write(row, col, "=F4/C4", cell_format2)
    row += 1
    worksheet.write(row, col, "=F5/C5", cell_format2)
    row += 1
    worksheet.write(row, col, "=F6/C6", cell_format2)
    row += 1
    worksheet.write(row, col, "=F7/C7", cell_format2)
    row += 1
    worksheet.write(row, col, "=F8/C8", cell_format2)

    # Column I (Average Surveyed Dam Density)

    row = 2
    col = 8
    worksheet.write(row, col, "=G3/C3", cell_format2)
    row += 1
    worksheet.write(row, col, "=G4/C4", cell_format2)
    row += 1
    worksheet.write(row, col, "=G5/C5", cell_format2)
    row += 1
    worksheet.write(row, col, "=G6/C6", cell_format2)
    row += 1
    worksheet.write(row, col, "=G7/C7", cell_format2)
    row += 1
    worksheet.write(row, col, "=G8/C8", cell_format2)

    # Column J (Percent Modeled Capacity)

    row = 2
    col = 9
    worksheet.write(row, col, "=IF(I3>0,H3/I3,\"N/A\")", percent2)
    row += 1
    worksheet.write(row, col, "=IF(I4>0,H4/I4,\"N/A\")", percent2)
    row += 1
    worksheet.write(row, col, "=IF(I5>0,H5/I5,\"N/A\")", percent2)
    row += 1
    worksheet.write(row, col, "=IF(I6>0,H6/I6,\"N/A\")", percent2)
    row += 1
    worksheet.write(row, col, "=IF(I7>0,H7/I7,\"N/A\")", percent2)
    row += 1
    worksheet.write(row, col, "=IF(I8>0,H8/I8,\"N/A\")", percent2)

    # Column K (Electivity Index)

    row = 2
    col = 10
    worksheet.write(row, col, "=(F3/$F$8) / E3", cell_format2)
    row += 1
    worksheet.write(row, col, "=(F4/$F$8) / E4", cell_format2)
    row += 1
    worksheet.write(row, col, "=(F5/$F$8) / E5", cell_format2)
    row += 1
    worksheet.write(row, col, "=(F6/$F$8) / E6", cell_format2)
    row += 1
    worksheet.write(row, col, "=(F7/$F$8) / E7", cell_format2)
    row += 1
    worksheet.write(row, col, "N/A", cell_format2)
    
def write_header(worksheet, watershed_name):
    row = 0
    col = 0
    worksheet.write(row, col, watershed_name)
    row += 1
    col += 1
    worksheet.write(row, col, "Stream Length (Km)")
    col += 1
    worksheet.write(row, col, "Stream Length (mi)")
    col += 1
    worksheet.write(row, col, "Percent")


def create_folder_structure(project_folder, summary_prods_folder):
    ai_folder = make_folder(summary_prods_folder, "AI")
    png_folder = make_folder(summary_prods_folder, "PNG")
    pdf_folder = make_folder(summary_prods_folder, "PDF")
    kmz_folder = make_folder(summary_prods_folder, "KMZ")
    lpk_folder = make_folder(summary_prods_folder, "LPK")

    ai_files = []
    png_files = []
    pdf_files = []
    kmz_files = []
    lpk_files = []
    
    for root, dirs, files in os.walk(project_folder):
        for file in files:
            file_path = os.path.join(root, file)
            if "\\SummaryProducts\\" in root:
                # We don't want to add anything that's already in our summary product area
                pass
            elif file.endswith(".ai"):
                ai_files.append(file_path)
            elif file.endswith(".png"):
                png_files.append(file_path)
            elif file.endswith(".pdf"):
                pdf_files.append(file_path)
            elif file.endswith(".kmz"):
                kmz_files.append(file_path)
            elif file.endswith(".lpk"):
                lpk_files.append(file_path)

    copy_all_files(ai_folder, ai_files)
    copy_all_files(kmz_folder, kmz_files)
    copy_all_files(lpk_folder, lpk_files)
    copy_to_input_output_structure(png_folder, png_files)
    copy_to_input_output_structure(pdf_folder, pdf_files)


def copy_to_input_output_structure(folder_base, files):
    """
    Copies our files into a "inputs, intermediates, outputs" folder structure
    :param folder_base: The base folder that we want to copy our files into
    :param files: A list of files that we want to copy
    :return:
    """
    output_folder = make_folder(folder_base, "Outputs")
    inputs_folder = make_folder(folder_base, "Inputs")
    intermed_folder = make_folder(folder_base, "Intermediates")

    for file in files:
        if "\\Inputs\\" in file:
            shutil.copy(file, inputs_folder)
        elif "\\01_Intermediates\\" in file:
            shutil.copy(file, intermed_folder)
        elif "\\02_Analyses\\" in file:
            shutil.copy(file, output_folder)
        else:
            shutil.copy(file, folder_base)


def copy_all_files(folder, files):
    for file in files:
        shutil.copy(file, folder)


if __name__ == "__main__":
    main(
        sys.argv[1],
        sys.argv[2],
        sys.argv[3],
        sys.argv[4])