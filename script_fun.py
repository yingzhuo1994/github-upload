import re, sys, operator

def get_tmatch(filename):
    """ tmatch uses a list to store timestamp and text information
        filename uses a format like "new.txt"
    """
    assert isinstance(filename, str)
    assert '.txt' in filename
    fhand = open(filename, 'rb')
    tmatch = []
    for line in fhand:
        # print(line)
        s = line.decode()
        # print(line, len(s), s[:-1].isdigit(), '\n', s)
        if s[:-1].isdigit():
            i = int(s[:-1]) - 1
            tmatch.append([])
        elif s != '\n':
            tmatch[i].append(s.replace('\n', ''))
        if len(tmatch[i]) > 2:
            tmatch[i][-2] = tmatch[i][-2] + ' ' + tmatch[i][-1]
            tmatch[i].pop()
        # newf = s
        # fnew.write(newf)
    s = [line for line in tmatch if len(line) > 1]

    wirte_script(s, 's')
    fhand.close()
    return s

def get_script(filename):
    """ Transform the script text to a list
        filename uses a format like "new.txt"
    """
    assert isinstance(filename, str)
    assert '.txt' in filename
    fhand = open(filename, 'rb')
    script = [line.decode().replace('\r\r\n','\n') for line in fhand]
    fhand.close()
    return script

def get_timestamp(time_str):
    """ Get the start and the end timestamp
    >>> t = '01:01:10,001 --> 01:01:10,002'
    ('01:01:10,001', '01:01:10,002')
    """
    assert '-->' in time_str
    t = time_str.split(' --> ')
    start = t[0]
    end = t[1]
    return start, end

def opt_timestamp(t1, t2, opt):
    """ Implement operations of add and sub for timestamp
        opt = add or sub
    """
    assert re.match(r'\d{1,2}:\d{1,2}:\d{1,2},\d{1,3}', t1)
    assert re.match(r'\d{1,2}:\d{1,2}:\d{1,2},\d{1,3}', t2)

    a = timestamp_to_time(t1)
    b = timestamp_to_time(t2)
    if opt == 'add':
        c = a + b
    if opt == 'sub':
        c = a - b
        if c < 0:
            print(t1, ' < ', t2, ' is not reasonable')
            return
    return time_to_timestamp(c)

def timestamp_to_time(timestamp):
    """ timestamp is a string: hh:mm:ss,sss
        time is a number: ss...
    >>> timestamp_to_time('01:01:10,001')
    3670001
    """
    assert re.match(r'\d{1,2}:\d{1,2}:\d{1,2},\d{1,3}', timestamp)
    lst = timestamp.split(':')
    sec = lst[2].split(',')
    # t = [int(lst[0]), int(lst[1]), int(sec[0]) * 1000 + int(sec[1])]
    t = (int(lst[0]) * 3600 + int(lst[1]) * 60 + int(sec[0])) * 1000 + int(sec[1])
    return t

def time_to_timestamp(time):
    """ time is a number: ss...   unit: millisecond
        timestamp is a string: hh:mm:ss,sss
    >>> time_to_timestamp(3670001)
    '01:01:10,001'
    """
    assert isinstance(time, int)
    h, m = time // 3600000, time % 3600000
    m, s = m // 60000, m % 60000
    a, b = s // 1000, s % 1000
    timestamp = str(h).zfill(2) + ':' + str(m).zfill(2) + ':'\
                + str(a).zfill(2) + ',' + str(b).zfill(3)
    return timestamp

def match_l(t_script, s_script, i, j, state, k):
    """ t_match is from tmatch, and i is its current line position
        s_script is from script, and j is its current line position
        state means the last state result of match_line
        -1, 0, 1 means t_match ends early, end at the same time, s_script ends early
        k is the word matching location, which is relevant to state value
    """
    t = t_script
    s = s_script

    def logic_check(t, s, i, j, state, k, f_b = 0):
        """ check whether t ends firstly
            f_b means check front or back ends firstly, 0 is front, 1 is back
        """
        if f_b == 1:
            state = -state
        m = 0
        accuracy = 0.8
        print(t[i], '\n', s[j])
        if state == 0:
            len_t = len(t[i])
            len_s = len(s[j])
            diff = len_t - len_s
            result = compare_line(t[i], s[j])
            # print(t[i], '\n', s[j])
            # print('result', result)
            if t[i][-1] == s[j][result[-1]] and diff < 1:
                k = result[-1]
                return True, k
        elif state == -1:
            len_t = len(t[i])
            len_s = len(s[j][k + 1:])
            diff = len_t - len_s
            result = compare_line(t[i], s[j][k + 1:])
            # print(result)
            if t[i][-1] == s[j][k + result[-1] + 1]:
                k = k + result[-1] + 1
                return True, k
        elif state == 1:
            len_t = len(t[i][k+1:])
            len_s = len(s[j])
            diff = len_t - len_s
            result = compare_line(t[i][k + 1:], s[j])
            # print(result)
            if t[i][-1] == s[j][result[-1]]:
                k = result[-1]
                return True, k
        # if m / len_t >= accuracy:

        return False, None

    a, x = logic_check(t, s, i, j, state, k, 0)
    print('t ends firstly？', a, x)
    b, y = logic_check(s, t, j, i, state, k, 1)
    print('s ends firstly？', b, y)
    if a and not b:
        return -1, x
    elif a and b:
        return 0, 0
    elif not a and b:
        return 1, y
    else:
        return None, None

def str_to_word(s):
    punct = '~`!#$%^&*()_+-=|\';":/.,?><~·！@#￥%……&*（）——+-=“：’；、。，？》《{}'
    s = re.sub(r"[%s]+" %punct, "", s).split()
    s = [c.lower() for c in s]
    return s

def compare_line(t, s):
    """ return the index list of the best matching sequence
    >>> t = ['c', 'g', 'e', 'a']
    >>> s = ['a', 'c', 'd', 'e', 'g', 'a']
    >>> compare_line(t, s)
    [1, 4, 5]
    """
    x, y = len(t), len(s)
    # if x > y:
    #     t, s = s, t
    #     x, y = y, x
    p = [[-1] for _ in range(x)]
    for i in range(x):
        for j in range(y):
            if t[i] == s[j]:
                if p[i][0] == -1:
                    p[i][0] = j
                else:
                    p[i].append(j)
    # print('p', p)
    count = []
    lst = combinelist(p)
    n = len(lst)
    for i in range(n):
        count += get_inclist(lst[i])
    # print('combined', lst, n)
    # print(count)
    result = get_contlist(count)
    print('longest list', result)
    return result
    # print(result)
    # for i in range(n):
    #     if count[i] == result:
    #         return lst[i]


def combinelist(lst):
    """ Combine all the number in lst
    >>> s = [[1, 2, 3]]
    >>> combinelist(s)
    [[1], [2], [3]]
    >>> lst = [[1], [2, 3], [4, 5]]
    >>> combinelist(lst)
    [[1, 2, 4], [1, 3, 4], [1, 2, 5], [1, 3, 5]]
    """
    n = len(lst)
    clst = []
    if n == 1:
        if len(lst[0]) == 1:
            return lst
        else:
            return [[k] for k in lst[0]]
    else:
        return [[k] + m for m in combinelist(lst[1:]) for k in lst[0]]

def incrlist(arr):
    """ Get the longest increating sub list
        from https://www.runoob.com/w3cnote/python-longest-increasing-subsequence.html
    >>> arr = [10, 22, 9, 33, 21, 50, 41, 60, 80]
    >>> incrlist(arr)
    [10, 22, 33, 50, 60, 80]
    """
    n = len(arr)
    m = [0]*n
    if n == 1:
        return arr
    for x in range(n-2,-1,-1):
        for y in range(n-1,x,-1):
            if arr[x] < arr[y] and m[x] <= m[y]:
                m[x] += 1
        max_value = max(m)
        result = []
        for i in range(n):
            if m[i] == max_value:
                result.append(arr[i])
                max_value -= 1
    return result

def get_inclist(s):
    """ get all the increasing sublist """
    def get_list(t):
        lst = []
        if not t:
            return [[]]
        else:
            a = [[t[0]] + k for k in get_list(t[1:])]
            b = get_list(t[1:])
            # print(a, b)
            return a + b
    # print(s)
    lst = get_list(s)
    # print(lst)
    lst.remove([])
    result = []
    for t in lst:
        n = len(t)
        if n <= 1:
            result.append(t)
        else:
            i = 0
            while i < n - 1:
                if t[i] >= t[i+1]:
                    break
                i += 1
            if i == n - 1:
                result.append(t)
    return result

def get_contlist(s):
    lst = max(s, key = lambda k: len(k))
    n = len(lst)
    m, goal = n * 100, [0]
    for t in s:
        if len(t) == n:
            diff = 0
            i = 0
            while i < n - 1:
                diff += t[i+1] - t[i]
                i += 1
            if m > diff or (m == diff and goal[-1] <= t[-1]):
                m = diff
                goal = t
    return goal


def time_calc(time, t_script, s_script, state, new_state, i, j, k, script):
    """ Calculate the start or end time of s_script from ts_match
        place = 0 or 1 (0 means start and 1 means end)
    """
    t, s = t_script[i], s_script[j]
    # print(t, '\n', s)
    t0, t1 = get_timestamp(time[i])
    time0, time1 = timestamp_to_time(t0), timestamp_to_time(t1)
    delta =  time1 - time0
    n = len(t)
    if n > 1:
        t_d = delta / (n - 1)
    else:
        t_d = 1
    # print('k', k)
    sec0 = time_to_timestamp(round(time1 - k * t_d) + 10) #calculated start time
    sec1 = time_to_timestamp(round(time0 + k * t_d) - 10) #calculated end time
    if new_state == -1:
        if state == 0:
            script[j][0] = t0 + ' --> '
        elif state == 1:
            script[j][0] = sec0 + ' --> '
    elif new_state == 0:
        if state == -1:
            script[j][0] += t1
        elif state == 0:
            script[j][0] = t0 + ' --> ' + t1
        elif state == 1:
            script[j][0] = sec0 + ' --> ' + t1
    elif new_state == 1:
        if state == -1:
            script[j][0] += sec1
        elif state == 0:
            script[j][0] = t0 + ' --> ' + sec1
        elif state == 1:
            sec0 = time_to_timestamp(round(timestamp_to_time(sec1) - (len(s) - 1 ) * t_d))
            script[j][0] = sec0 + ' --> ' + sec1

    # return time_to_timestamp(round(time))
    return script[j][0]

def match_s(tmatch, script):
    """ Add timestamp to script
    """
    time = []
    t_script = []
    for line in tmatch:
        time.append(line[0])
        t_script.append(str_to_word(line[1]))
        # print(line)
    s_script = [str_to_word(s) for s in script]
    i, j = 0, 0
    state, k = 0, 0
    s = [['time', script[k]] for k in range(len(script))]
    while i < len(t_script) and j < len(script):
        print('state:', state, 'k:', k)
        new_state, k = match_l(t_script, s_script, i, j, state, k)
        # print('new_state', new_state, k)
        time_calc(time, t_script, s_script, state, new_state, i, j, k, s)
        if new_state == -1:
            i += 1
        elif new_state == 0:
            i += 1
            j += 1
        elif new_state == 1:
            j += 1
        else:
            print('An error happened in line ', i+1, '\n', tmatch[i][1], '\n', script[j])
            print(state, new_state)
            sys.exit()
        state = new_state
    return s


def wirte_script(script_time, filename):
    fhand = open(filename + '.txt', 'a', encoding='utf-8')
    fhand.seek(0)
    fhand.truncate()
    n = len(script_time)
    for i in range(n):
        s = ''
        s += str(i+1) + '\n'
        s += script_time[i][0] + '\n'
        s += script_time[i][1] + '\n\n'
        # print(s)
        fhand.write(s)
    fhand.close()

def for_display(lst):
    """ Display each line of the lst seperately
    """
    assert isinstance(lst, list)
    for s in lst:
        print(s.__repr__())
