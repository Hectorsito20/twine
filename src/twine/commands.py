"""
Implementation of all of the individual 'twine' commands available through
twine-sh.
"""

import sys

OUT=None
ERR=sys.stderr

# export:
__all__ = ['get_browser',
           'reset_browser',
           'extend_with',
           'exit',
           'go',
           'reload',
           'url',
           'code',
           'follow',
           'find',
           'notfind',
           'back',
           'show',
           'echo',
           'save_html',
           'sleep',
           'agent',
           'showforms',
           'showlinks',
           'showhistory',
           'submit',
           'formvalue',
           'fv',
           'formaction',
           'fa',
           'formclear',
           'formfile',
           'getinput',
           'getpassword',
           'save_cookies',
           'load_cookies',
           'clear_cookies',
           'show_cookies',
           'add_auth',
           'run_python',
           'run',
           'runfile',
           'setglobal',
           'setlocal',
           'debug',
           'title',
           'exit',
           'config',
           'tidy_ok',
           'redirect_output',
           'reset_output',
           'redirect_error',
           'reset_error',
           'add_extra_header',
           'show_extra_headers',
           'clear_extra_headers',
           'info',
           'browse',
           'run_javascript',
           'save_screenshot'
           ]

import re, getpass, time

from errors import TwineException, TwineAssertionError
import utils
from utils import make_boolean, set_form_control_value, run_tidy
from namespaces import get_twine_glocals

from browser import TwineBrowser
import spynner
import pyquery
import urlparse

browser = TwineBrowser(debug_level = spynner.ERROR)
browser.set_html_parser(pyquery.PyQuery)

def get_browser():
    return browser

def reset_browser():
    """
    >> reset_browser

    Reset the browser completely.
    """
    global browser

    browser = TwineBrowser(debug_level = spynner.ERROR)
    browser.set_html_parser(pyquery.PyQuery)

def exit(code = "0"):
    """
    exit [<code>]

    Exits twine, with the given exit code (defaults to 0, "no error").
    """
    raise SystemExit(int(code))

def go(url):
    """
    >> go <url>

    Visit the URL given.
    """
    success = browser.go(url)

    if success:
        print>>OUT, '==> at', browser.url
    else:
        raise TwineException("cannot go to '%s'" % (url,))

    return browser.url

def reload():
    """
    >> reload

    Reload the current URL.
    """
    browser.load(browser.url, False)
    print>>OUT, '==> reloaded'

def code(should_be):
    """
    >> code <int>
    
    Check to make sure the response code for the last page is as given.
    """
    actual = browser.http_status or "None"
    if actual != should_be:
        raise TwineAssertionError("code is %s != %s" % (actual,
                                                        should_be))

def tidy_ok():
    """
    >> tidy_ok

    Assert that 'tidy' produces no warnings or errors when run on the current
    page.

    If 'tidy' cannot be run, will fail silently (unless 'tidy_should_exist'
    option is true; see 'config' command).
    """
    raise TwineAssertionError("Not yet implemented")

def url(should_be):
    """
    >> url <regexp>

    Check to make sure that the current URL matches the regexp.  The local
    variable __match__ is set to the matching part of the URL.
    """
    regexp = re.compile(should_be)
    current_url = browser.url

    m = None
    if current_url is not None:
        m = regexp.search(current_url)
    else:
        current_url = ''

    if not m:
        raise TwineAssertionError("""\
current url is '%s';
does not match '%s'
""" % (current_url, should_be,))

    if m.groups():
        match_str = m.group(1)
    else:
        match_str = m.group(0)

    global_dict, local_dict = get_twine_glocals()
    local_dict['__match__'] = match_str
    return match_str

def follow(what):
    """
    >> follow <regexp>
    
    Find the first matching link on the page & visit it.
    """
    regexp = re.compile(what)
    links = [
             (l.text or '', l.get("href"))
             for l in browser.soup("a")
            ]
    found_link = ''
    for link in links:
        if re.search(regexp, link[0]) or re.search(regexp, link[1]):
            found_link = link[1]
            break

    if found_link != '':
        browser.go(found_link)
        print>>OUT, '==> at', browser.url
        return browser.url

    raise TwineAssertionError("no links match to '%s'" % (what,))

def _parseFindFlags(flags):
    KNOWN_FLAGS = {
        'i': re.IGNORECASE,
        'm': re.MULTILINE,
        's': re.DOTALL,
        }
    finalFlags = 0
    for char in flags:
        try:
            finalFlags |= KNOWN_FLAGS[char]
        except IndexError:
            raise TwineAssertionError("unknown 'find' flag %r" % char)
    return finalFlags

def find(what, flags=''):
    """
    >> find <regexp> [<flags>]
    
    Succeed if the regular expression is on the page.  Sets the local
    variable __match__ to the matching text.

    Flags is a string consisting of the following characters:

    * i: ignorecase
    * m: multiline
    * s: dotall

    For explanations of these, please see the Python re module
    documentation.
    """
    regexp = re.compile(what, _parseFindFlags(flags))
    page = browser.html

    m = regexp.search(page)
    if not m:
        raise TwineAssertionError("no match to '%s'" % (what,))

    if m.groups():
        match_str = m.group(1)
    else:
        match_str = m.group(0)

    _, local_dict = get_twine_glocals()
    local_dict['__match__'] = match_str

def notfind(what, flags=''):
    """
    >> notfind <regexp> [<flags>]
    
    Fail if the regular expression is on the page.
    """
    regexp = re.compile(what, _parseFindFlags(flags))
    page = browser.html

    if regexp.search(page):
        raise TwineAssertionError("match to '%s'" % (what,))

def back():
    """
    >> back
    
    Return to the previous page.
    """
    if browser.back():
        print>>OUT, '==> back to', browser.url
    else:
        print>>OUT, '==> back at empty page.'

def show():
    """
    >> show
    
    Show the HTML for the current page.
    """
    html = browser.html
    print>>OUT, html
    return html

def echo(*strs):
    """
    >> echo <list> <of> <strings>
    
    Echo the arguments to the screen.
    """
    strs = map(str, strs)
    s = " ".join(strs)
    print>>OUT, s

def save_html(filename=None):
    """
    >> save_html [<filename>]
    
    Save the HTML for the current page into <filename>.  If no filename
    given, construct the filename from the URL.
    """
    html = browser.html
    if html is None:
        print>>OUT, "No page to save."
        return

    if filename is None:
        url = b.url
        url = url.split('?')[0]
        filename = url.split('/')[-1]
        if filename is "":
            filename = 'index.html'

        print>>OUT, "(Using filename '%s')" % (filename,)

    f = open(filename, 'w')
    f.write(html)
    f.close()

def sleep(interval=1):
    """
    >> sleep [<interval>]

    Sleep for the specified amount of time.
    If no interval is given, sleep for 1 second.
    """
    time.sleep(float(interval))

def agent(agent_string):
    """
    >> agent <agent_string>
    
    Set the agent string (identifying the browser brand).

    """
    browser.add_header(("User-Agent", agent_string))

def submit(submit_button=None):
    """
    >> submit [<buttonspec>]
    
    Submit the current form (the one last clicked on) by clicking on the
    n'th submission button.  If no "buttonspec" is given, submit the current
    form by using the last clicked submit button.

    The form to submit is the last form clicked on with a 'formvalue' command.

    The button used to submit is chosen based on 'buttonspec'.  If 'buttonspec'
    is given, it's matched against buttons using the same rules that
    'formvalue' uses.  If 'buttonspec' is not given, submit uses the last
    submit button clicked on by 'formvalue'.  If none can be found,
    submit submits the form with no submit button clicked.
    """
    if submit_button:
        raise TwineAssertionError("Not yet implemented")

    if browser.last_form is None:
        raise TwineAssertionError("No default submit available")

    formname = browser.last_form
    form, form_number = browser.find_form(browser.last_form)

    submits = [ i for i in form.find("input[type=submit]").items() ]

    if not submits:
        raise TwineAssertionError("form has no submit button")

    button = submits[0]

    # This only works for submit buttons with a value for now
    if button.attr.value:
        browser.submit("input[value=%s]" % button.attr.value)
    else:
        raise TwineAssertionError("Not yet implemented")

def _trunc(s, length):
    """
    Truncate a string s to length length, by cutting off the last 
    (length-4) characters and replacing them with ' ...'
    """
    if not s:
        return ''
    
    if len(s) > length:
        return s[:length - 4] + ' ...'
    
    return s

def showforms():
    """
    >> showforms
    
    Show all of the forms on the current page.
    """
    for i, form in enumerate(browser.soup("form").items()):
        # Group radio fields
        radio_options = [ f for f in form.find("input").items()
                          if f.attr.type == "radio" ]

        radio_fields = {}
        for radio_option in radio_options:
            name = radio_option.attr.name
            if name in radio_fields:
                radio_fields[name].append(radio_option.attr.value)
            else:
                radio_fields[name] = [radio_option.attr.value]

        if form.attr.name:
            print>>OUT, "Form name=%s (#%d)" % (form.attr.name, i + 1,)
        else:
            print>>OUT, "Form #%d" % (i + 1,)

        # Form fields(input and select)
        fields = [ i for i in form.find("input").items() ]
        fields.extend([ i for i in form.find("select").items() ])
        fields.extend([ i for i in form.find("textarea").items() ])

        if fields:
            print>>OUT, "## ## __Name__________________ __Type___ __ID________ __Value__________________"

            submit_number = 1
            for j, field in enumerate(fields):
                # Skip this field if it's part of a radio group already printed
                if field.attr.type == "radio" and \
                   field.attr.name not in radio_fields:
                       continue

                if field.attr.type == "submit":
                    # Print form number
                    print>>OUT, ("%-2s" % (j + 1,)),

                    # If submit, print submit number
                    print>>OUT, ("%-2s" % submit_number),
                    submit_number += 1
                else:
                    # Print form number
                    print>>OUT, ("%-5s" % (j + 1,)),

                # Print form name
                print>>OUT, ("%-23s " % (_trunc(field.attr.name, 23),)),

                # Print form type
                if field.is_("input"):
                    if field.attr.type:
                        print>>OUT, ("%-9s" % (_trunc(field.attr.type, 9))),
                    else:
                        print>>OUT, ("%-9s" % "text"),
                elif field.is_("textarea"):
                    print>>OUT, ("%-9s" % "textarea"),
                elif field.is_("select"):
                    print>>OUT, ("%-9s" % "select"),

                # Print form ID
                form_id = _trunc(field.attr.id, 12) or "(None)"
                print>>OUT, ("%-12s" % form_id),

                # Print form value, or options
                if field.is_("select"):
                    options = field.find("option").items()
                    option_values = [ o.attr.value
                                      for o in field.find("option").items() ]

                    # FIX: select names aren't necessarily unique
                    selector = "select[name=%s]" % field.attr.name
                    jsc = "console.log($('%s').val())" % selector
                    selected_option = browser.run_javascript(jsc)

                    value = "['%s'] of %s" % (selected_option, option_values,)
                    print>>OUT, _trunc(value, 40)
                elif field.is_("textarea"):
                    # FIX: textarea names aren't necessarily unique
                    selector = "textarea[name=%s]" % field.attr.name
                    jsc = "console.log($('%s').val())" % selector
                    print>>OUT, browser.run_javascript(jsc)
                else:
                    if field.attr.type == "submit":
                        print>>OUT, _trunc(field.attr.value, 40)
                    elif field.attr.type == "radio":
                        selector = "input[name=%s]:checked" % field.attr.name
                        jsc = "console.log($('%s').val())" % selector
                        selected_option = browser.run_javascript(jsc)

                        radio_values = radio_fields[field.attr.name]

                        value = "['%s'] of %s" % (selected_option,
                                                  radio_values,)
                        print>>OUT, _trunc(value, 40)

                        del radio_fields[field.attr.name]
                    elif field.attr.type == "checkbox":
                        selector = "input[name=%s]" % field.attr.name
                        jsc = "console.log($('%s').attr('checked'))" % selector
                        checked_status = browser.run_javascript(jsc)
                        if checked_status == "true":
                            print>>OUT, "checked"
                        else:
                            print>>OUT, "unchecked"

                    else:
                        # FIX: input names aren't necessarily unique
                        selector = "input[name=%s]" % field.attr.name
                        jsc = "console.log($('%s').val())" % selector
                        print>>OUT, browser.run_javascript(jsc)

def showlinks():
    """
    >> showlinks
    
    Show all of the links on the current page.
    """
    for n, link in enumerate(browser.soup("a").items()):
        print>>OUT, "%d. %s ==> %s" % (n, link.text(), link.attr.href,)
    print>>OUT, ''

def showhistory():
    """
    >> showhistory

    Show the browser history (what URLs were visited).
    """
    history = browser.history

    print>>OUT, ''
    if browser.url == '':
        print>>OUT, 'History: (%d pages total) ' % (len(history))
    else:
        print>>OUT, 'History: (%d pages total) ' % (len(history) + 1)


    for n, page in enumerate(history):
        print>>OUT, "\t%d. %s" % (n + 1, page)

    print>>OUT, ''

    return history

def formclear(formname):
    """
    >> formclear <formname>
    
    Run 'clear' on all of the controls in this form.
    """
    browser.formclear(formname)

def formvalue(formname, fieldname, value):
    """
    >> formvalue <formname> <field> <value>

    Set value of a form field.

    There are some ambiguities in the way formvalue deals with lists:
    'formvalue' will *add* the given value to a list of multiple selection,
    for lists that allow it.

    Forms are matched against 'formname' as follows:
      1. regexp match to actual form name;
      2. if 'formname' is an integer, it's tried as an index.

    Form controls are matched against 'fieldname' as follows:
      1. unique exact match to control name;
      2. unique regexp match to control name;
      3. if fieldname is an integer, it's tried as an index;
      4. unique & exact match to submit-button values.

    Formvalue ignores read-only fields completely; if they're readonly,
    nothing is done, unless the config options ('config' command) are
    changed.

    'formvalue' is available as 'fv' as well.
    """
    browser.formvalue(formname, fieldname, value)

fv = formvalue

def formaction(formname, action):
    """
    >> formaction <formname> <action_url>

    Sets action parameter on form to action_url
    """
    form, form_number = browser.find_form(formname)
    if form.attr.name:
        jscode = "$('form[name=%s]').attr('action', '%s');" % (form.attr.name,
                                                               action,)
        browser.run_javascript(jscode)
    try:
        formname = int(formname)
        formname -= 1

        all_forms = [ i for i in browser.soup("form").items() ]

        if len(all_forms) > formname:
            form = all_forms[formname]
        else:
            raise TwineAssertionError("no matching forms!")

        jscode = "$('form')[%s].attr('action', '%s');" % (str(formname),
                                                          action,)
        browser.run_javascript(jscode)

    except ValueError:
        raise TwineAssertionError("no matching forms!")

fa = formaction

def formfile(formname, fieldname, filename, content_type=None):
    """
    >> formfile <form> <field> <filename> [ <content_type> ]

    Upload a file via an "upload file" form field.
    """
    raise TwineAssertionError("Not yet implemented")

def extend_with(module_name):
    """
    >> extend_with <module>
    
    Import contents of given module.
    """
    raise TwineAssertionError("Not yet implemented")

def getinput(prompt):
    """
    >> getinput <prompt>

    Get input, store it in '__input__'.
    """
    local_dict = get_twill_glocals()[1]
    inp = raw_input(prompt)
    local_dict['__input__'] = inp
    return inp

def getpassword(prompt):
    """
    >> getpassword <prompt>

    Get a password ("invisible input"), store it in '__password__'.
    """
    local_dict = get_twill_glocals()[1]
    inp = getpass.getpass(prompt)
    local_dict['__password__'] = inp
    return inp

def save_cookies(filename):
    """
    >> save_cookies <filename>

    Save all of the current cookies to the given file.
    """
    fp = open(filename, 'wb')
    fp.write(browser.get_cookies())

def load_cookies(filename):
    """
    >> load_cookies <filename>

    Clear the cookie jar and load cookies from the given file.
    """
    fp = open(filename, 'rb')
    browser.set_cookies(fp.read())

def clear_cookies():
    """
    >> clear_cookies

    Clear the cookie jar.
    """
    browser.set_cookies('')

def show_cookies():
    """
    >> show_cookies

    Show all of the cookies in the cookie jar.
    """
    # Cookies stored in Mozilla format
    cookies = browser.get_cookies().split("\n")[2:]

    print>>OUT, 'There are %d cookie(s) in the cookiejar.\n' % (len(cookies))

    if len(cookies):
        for cookie in cookies:
            cookie = cookie.split("\t")
            print>>OUT, "\t<Cookie %s=%s for %s/>" % (cookie[5], cookie[6],
                                                      cookie[0])

        print>>OUT, ''
    

def add_auth(realm, uri, user, passwd):
    """
    >> add_auth <realm> <uri> <user> <passwd>

    Add HTTP Basic Authentication information for the given realm/uri.

    """
    browser.add_credentials(realm, uri, user, passwd)

def debug(what, level):
    """
    >> debug <what> <level>

    <what> can be:
       * http (any level >= 1), to display the HTTP transactions.
       * commands (any level >= 1), to display the commands being executed.
       * equiv-refresh (any level >= 1) to display HTTP-EQUIV refresh handling.
    """
    raise TwineAssertionError("Not yet implemented")

def run_python(cmd):
    """
    >> run_python <command>

    <command> can be any valid python command; 'exec' is used to run it.
    """
    global_dict, local_dict = get_twine_glocals()

    import commands

    # set __url__
    local_dict['__cmd__'] = cmd
    local_dict['__url__'] = commands.browser.url

    exec(cmd, global_dict, local_dict)

run = run_python

def runfile(*files):
    """
    >> runfile <file1> [ <file2> ... ]

    """
    import parse
    global_dict, local_dict = get_twine_glocals()

    for f in files:
        parse.execute_file(f, no_reset=True)

def setglobal(name, value):
    """
    setglobal <name> <value>

    Sets the variable <name> to the value <value> in the global namespace.
    """
    global_dict, local_dict = get_twine_glocals()
    global_dict[name] = value

def setlocal(name, value):
    """
    setlocal <name> <value>

    Sets the variable <name> to the value <value> in the local namespace.
    """
    global_dict, local_dict = get_twine_glocals()
    local_dict[name] = value

def title(what):
    """
    >> title <regexp>
    
    Succeed if the regular expression is in the page title.
    """
    regexp = re.compile(what)
    title = browser.title

    print>>OUT, "title is '%s'." % (title,)

    m = regexp.search(title)
    if not m:
        raise TwineAssertionError("title does not contain '%s'" % (what,))

def redirect_output(filename):
    """
    >> redirect_output <filename>

    Append all twine output to the given file.
    """
    import twine
    fp = open(filename, 'a')
    twine.set_output(fp)

def reset_output():
    """
    >> reset_output

    Reset twine output to go to the screen.
    """
    import twine
    twine.set_output(None)

def redirect_error(filename):
    """
    >> redirect_error <filename>

    Append all twine error output to the given file.
    """
    import twine
    fp = open(filename, 'a')
    twine.set_output(fp)

def reset_error():
    """
    >> reset_error
    
    Reset twine error output to go to the screen.
    """
    import twine
    twine.set_output(None)

def add_extra_header(header_key, header_value):
    """
    >> add_header <name> <value>

    Add an HTTP header to each HTTP request.  See 'show_extra_headers' and
    'clear_extra_headers'.
    """
    browser.add_header((header_key, header_value))

def show_extra_headers():
    """
    >> show_extra_headers

    Show any extra headers being added to each HTTP request.
    """
    headers = browser.headers
    if headers:
        print 'The following HTTP headers are added to each request:'
    
        for k, v in headers:
            print '  "%s" = "%s"' % (k, v,)
            
        print ''
    else:
        print '** no extra HTTP headers **'

def clear_extra_headers():
    """
    >> clear_extra_headers

    Remove all user-defined HTTP headers.  See 'add_extra_header' and
    'show_extra_headers'.
    """
    browser.reset_headers()

_orig_options = dict(readonly_controls_writeable=False,
                     use_tidy=True,
                     require_tidy=False,
                     use_BeautifulSoup=True,
                     require_BeautifulSoup=False,
                     allow_parse_errors=True,
                     with_default_realm=False,
                     acknowledge_equiv_refresh=True
                     )

_options = {}
_options.update(_orig_options)

def config(key=None, value=None):
    """
    >> config [<key> [<int value>]]

    Configure/report various options.  If no <value> is given, report
    the current key value; if no <key> given, report current settings.

    So far:

     * 'acknowledge_equiv_refresh', default 1 -- follow HTTP-EQUIV=REFRESH
     * 'readonly_controls_writeable', default 0 -- make ro controls writeable
     * 'require_tidy', default 0 -- *require* that tidy be installed
     * 'use_BeautifulSoup', default 1 -- use the BeautifulSoup parser
     * 'use_tidy', default 1 -- use tidy, if it's installed
     * 'with_default_realm', default 0 -- use a default realm for HTTP AUTH

    Deprecated:
     * 'allow_parse_errors' has been removed.
    """
    if key is None:
        keys = _options.keys()
        keys.sort()

        print>>OUT, 'current configuration:'
        for k in keys:
            print>>OUT, '\t%s : %s' % (k, _options[k])
        print>>OUT, ''
    else:
        v = _options.get(key)
        if v is None:
            print>>OUT, '*** no such configuration key', key
            print>>OUT, 'valid keys are:', ";".join(_options.keys())
            raise TwineException('no such configuration key: %s' % (key,))
        elif value is None:
            print>>OUT, ''
            print>>OUT, 'key %s: value %s' % (key, v)
            print>>OUT, ''
        else:
            value = make_boolean(value)
            _options[key] = value

def info():
    """
    >> info

    Report information on current page.
    """
    current_url = browser.url
    if current_url == "":
        print "We're not on a page!"
        return

    content_type = browser.content_type

    check_html = False
    if content_type.startswith('text/html'):
        check_html = True

    code = browser.http_status

    print >>OUT, '\nPage information:'
    print >>OUT, '\tURL:', current_url
    print >>OUT, '\tHTTP code:', code
    print >>OUT, '\tContent type:', content_type,

    if check_html:
        print >>OUT, '(HTML)'
    else:
        print ''

    if check_html:
        title = browser.title
        print >>OUT, '\tPage title:', title

        form_count = len(browser.soup("form"))
        if form_count:
            print >>OUT, '\tThis page contains %d form(s)' % (form_count,)

    print >>OUT, ''

def browse():
    """
    >> browse

    Allows the user to browse the current page. Returns when the window
    is closed.
    """
    browser.browse()

def run_javascript(code):
    """
    >> run_javascript <code>

    Runs JavaScript code.
    """
    output = browser.run_javascript(code)
    if output:
        print "Javascript console:", output

def save_screenshot(filename):
    """
    >> save_screenshot <filename>

    Saves a screenshot of the current page. File format dependent on
    the filename extension.
    """
    browser.snapshot().save(filename)
