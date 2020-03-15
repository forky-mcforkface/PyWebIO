r"""输出内容到用户浏览器

本模块提供了一系列函数来输出不同形式的内容到用户浏览器，并支持灵活的输出控制。

输出控制
--------------

锚点
^^^^^^^^^^^^^^^^^

.. autofunction:: set_anchor
.. autofunction:: clear_before
.. autofunction:: clear_after
.. autofunction:: clear_range
.. autofunction:: scroll_to

环境设置
^^^^^^^^^^^^^^^^^

.. autofunction:: set_title
.. autofunction:: set_output_fixed_height
.. autofunction:: set_auto_scroll_bottom

内容输出
--------------
.. autofunction:: put_text
.. autofunction:: put_markdown
.. autofunction:: put_code
.. autofunction:: put_table
.. autofunction:: td_buttons
.. autofunction:: put_buttons
.. autofunction:: put_file
"""
from base64 import b64encode
from collections.abc import Mapping

from .framework import Global
from .io_ctrl import output_register_callback, send_msg


def set_title(title):
    r"""设置页面标题"""
    send_msg('output_ctl', dict(title=title))


def set_output_fixed_height(enabled=True):
    r"""开启/关闭页面固高度模式"""
    send_msg('output_ctl', dict(output_fixed_height=enabled))


def set_auto_scroll_bottom(enabled=True):
    r"""开启/关闭页面自动滚动到底部"""
    send_msg('output_ctl', dict(auto_scroll_bottom=enabled))


_AnchorTPL = 'pywebio-anchor-%s'


def set_anchor(name):
    """
    在当前输出处标记锚点。 若已经存在 ``name`` 锚点，则先将旧锚点删除
    """
    inner_ancher_name = _AnchorTPL % name
    send_msg('output_ctl', dict(set_anchor=inner_ancher_name))


def clear_before(anchor):
    """清除 ``anchor`` 锚点之前输出的内容"""
    inner_ancher_name = _AnchorTPL % anchor
    send_msg('output_ctl', dict(clear_before=inner_ancher_name))


def clear_after(anchor):
    """清除 ``anchor`` 锚点之后输出的内容"""
    inner_ancher_name = _AnchorTPL % anchor
    send_msg('output_ctl', dict(clear_after=inner_ancher_name))


def clear_range(start_anchor, end_anchor):
    """
    清除 ``start_anchor`` - ``end_ancher`` 锚点之间输出的内容.
    若 ``start_anchor`` 或 ``end_ancher`` 不存在，则不进行任何操作
    """
    inner_start_anchor_name = 'pywebio-anchor-%s' % start_anchor
    inner_end_ancher_name = 'pywebio-anchor-%s' % end_anchor
    send_msg('output_ctl', dict(clear_range=[inner_start_anchor_name, inner_end_ancher_name]))


def scroll_to(anchor):
    """将页面滚动到 ``anchor`` 锚点处"""
    inner_ancher_name = 'pywebio-anchor-%s' % anchor
    send_msg('output_ctl', dict(scroll_to=inner_ancher_name))


def _put_content(type, ws=None, anchor=None, before=None, after=None, **other_spec):
    """
    向用户端发送 ``output`` 指令

    :param type: 输出类型
    :param content: 输出内容
    :param anchor: 为当前的输出内容标记锚点
    :param before: 在给定的锚点之前输出内容
    :param after: 在给定的锚点之后输出内容。
        注意： ``before`` 和 ``after`` 参数不可以同时使用
    :param other_spec: 额外的输出参数
    """
    assert not (before and after), "Parameter 'before' and 'after' cannot be specified at the same time"

    spec = dict(type=type)
    spec.update(other_spec)
    if anchor:
        spec['anchor'] = _AnchorTPL % anchor
    if before:
        spec['before'] = _AnchorTPL % before
    elif after:
        spec['after'] = _AnchorTPL % after

    msg = dict(command="output", spec=spec)
    (ws or Global.active_ws).add_server_msg(msg)


def put_text(text, inline=False, anchor=None, before=None, after=None):
    """
    输出文本内容

    :param str text: 文本内容
    :param str anchor: 为当前的输出内容标记锚点
    :param str before: 在给定的锚点之前输出内容
    :param str after: 在给定的锚点之后输出内容
        注意： ``before`` 和 ``after`` 参数不可以同时使用
    """
    _put_content('text', content=text, inline=inline, anchor=anchor, before=before, after=after)


def put_html(html, anchor=None, before=None, after=None):
    """
    输出文本内容

    :param str html: html内容
    :param str anchor, before, after: 与 `put_text` 函数的同名参数含义一致
    """
    _put_content('html', content=html, anchor=anchor, before=before, after=after)


def put_code(content, langage='', anchor=None, before=None, after=None):
    """
    输出代码块

    :param str content: 代码内容
    :param str langage: 代码语言
    :param str anchor, before, after: 与 `put_text` 函数的同名参数含义一致
    """
    code = "```%s\n%s\n```" % (langage, content)
    put_markdown(code, anchor=anchor, before=before, after=after)


def put_markdown(mdcontent, strip_indent=0, lstrip=False, anchor=None, before=None, after=None):
    """
    输出Markdown内容。


    :param str mdcontent: Markdown文本
    :param int strip_indent: 对于每一行，若前 ``strip_indent`` 个字符都为空格，则将其去除
    :param bool lstrip: 是否去除每一行开始的空白符
    :param str anchor, before, after: 与 `put_text` 函数的同名参数含义一致

    当在函数中使用Python的三引号语法输出多行内容时，为了排版美观可能会对Markdown文本进行缩进，
    这时候，可以设置 ``strip_indent`` 或 ``lstrip`` 来防止Markdown错误解析(但不要同时使用 ``strip_indent`` 和 ``lstrip`` )::

        # 不使用strip_indent或lstrip
        def hello():
            put_markdown(r\""" # H1
        This is content.
        \""")

        # 使用lstrip
        def hello():
            put_markdown(r\""" # H1
            This is content.
            \""", lstrip=True)

        # 使用strip_indent
        def hello():
            put_markdown(r\""" # H1
            This is content.
            \""", strip_indent=4)
    """
    if strip_indent:
        lines = (
            i[strip_indent:] if (i[:strip_indent] == ' ' * strip_indent) else i
            for i in mdcontent.splitlines()
        )
        mdcontent = '\n'.join(lines)
    if lstrip:
        lines = (i.lstrip() for i in mdcontent.splitlines())
        mdcontent = '\n'.join(lines)

    _put_content('markdown', content=mdcontent, anchor=anchor, before=before, after=after)


def put_table(tdata, header=None, anchor=None, before=None, after=None):
    """
    输出表格

    :param list tdata: 表格数据。列表项可以为 ``list`` 或者 ``dict``
    :param list header: 当tdata为字典列表时，使用 ``header`` 指定表头顺序
    :param str anchor, before, after: 与 `put_text` 函数的同名参数含义一致
    """
    if header:
        tdata = [
            [row.get(k, '') for k in header]
            for row in tdata
        ]

    def quote(data):
        return str(data).replace('|', r'\|')

    # 防止当tdata只有一行时，无法显示表格
    if len(tdata) == 1:
        tdata[0:0] = [' '] * len(tdata[0])

    header = "|%s|" % "|".join(map(quote, tdata[0]))
    res = [header]
    res.append("|%s|" % "|".join(['----'] * len(tdata[0])))
    for tr in tdata[1:]:
        t = "|%s|" % "|".join(map(quote, tr))
        res.append(t)
    put_markdown('\n'.join(res), anchor=anchor, before=before, after=after)


def _format_button(buttons):
    """
    格式化按钮参数
    :param buttons: button列表， button可用形式：
        {value:, label:, }
        (value, label,)
        value 单值，label等于value

    :return: [{value:, label:, }, ...]
    """

    btns = []
    for btn in buttons:
        if isinstance(btn, Mapping):
            assert 'value' in btn and 'label' in btn, 'actions item must have value and label key'
        elif isinstance(btn, list):
            assert len(btn) == 2, 'actions item format error'
            btn = dict(zip(('value', 'label'), btn))
        else:
            btn = dict(value=btn, label=btn)
        btns.append(btn)
    return btns


def td_buttons(buttons, onclick, save=None, mutex_mode=False):
    """
    在表格中显示一组按钮

    :param str buttons, onclick, save: 与 `put_buttons` 函数的同名参数含义一致
    """
    btns = _format_button(buttons)
    callback_id = output_register_callback(onclick, save, mutex_mode)
    tpl = '<button type="button" value="{value}" class="btn btn-primary btn-sm" ' \
          'onclick="WebIO.DisplayAreaButtonOnClick(this, \'%s\')">{label}</button>' % callback_id
    btns_html = [tpl.format(**b) for b in btns]
    return ' '.join(btns_html)


def put_buttons(buttons, onclick, small=False, save=None, mutex_mode=False, anchor=None, before=None, after=None):
    """
    输出一组按钮

    :param list buttons: 按钮列表。列表项的可用形式有：

        * dict: ``{value:选项值, label:选项标签, [disabled:是否禁止点击]}``
        * tuple or list: ``(value, label, [disabled])``
        * 单值: 此时label和value使用相同的值

    :type onclick: Callable or Coroutine
    :param onclick: 按钮点击回调函数. ``onclick`` 可以是普通函数或者协程函数.
        函数签名为 ``onclick(btn_value, save)``.
        当按钮组中的按钮被点击时，``onclick`` 被调用，``onclick`` 接收两个参数，``btn_value``为被点击的按钮的 ``value`` 值，
        ``save`` 为 `td_buttons` 的 ``save`` 参数值
    :param any save: ``save`` 内容将传入 ``onclick`` 回调函数的第二个参数
    :param bool mutex_mode: 互斥模式。若为 ``True`` ，则在运行回调函数过程中，无法响应当前按钮组的新点击事件，仅当 `onclick`` 为协程函数时有效
    :param str anchor, before, after: 与 `put_text` 函数的同名参数含义一致
    """
    assert not (before and after), "Parameter 'before' and 'after' cannot be specified at the same time"
    btns = _format_button(buttons)
    callback_id = output_register_callback(onclick, save, mutex_mode)
    _put_content('buttons', callback_id=callback_id, buttons=btns, small=small, anchor=anchor, before=before,
                 after=after)


def put_file(name, content, anchor=None, before=None, after=None):
    """输出文件。
    在浏览器上的显示为一个以文件名为名的链接，点击链接后浏览器自动下载文件。

    :param str name: 文件名
    :param content: 文件内容. 类型为 bytes-like object
    :param str anchor, before, after: 与 `put_text` 函数的同名参数含义一致
    """
    assert not (before and after), "Parameter 'before' and 'after' cannot be specified at the same time"
    content = b64encode(content).decode('ascii')
    _put_content('file', name=name, content=content, anchor=anchor, before=before, after=after)