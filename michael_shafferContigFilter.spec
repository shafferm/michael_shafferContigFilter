/*
A KBase module: michael_shafferContigFilter
This sample module contains one small method that filters contigs.
*/

module michael_shafferContigFilter {
    typedef structure {
        string report_name;
        string report_ref;
    } ReportResults;

    /*
        This example function accepts any number of parameters and returns results in a KBaseReport
    */
    funcdef run_michael_shafferContigFilter(mapping<string,UnspecifiedObject> params) returns (ReportResults output) authentication required;

    funcdef run_michael_shafferContigFilter_max(mapping<string,UnspecifiedObject> params) returns (ReportResults output) authentication required;
};
