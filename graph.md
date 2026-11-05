---
config:
  flowchart:
    curve: linear
---
graph TD;
        __start__([<p>__start__</p>]):::first
        chat_node(chat_node)
        tools(tools)
        __end__([<p>__end__</p>]):::last
        __start__ --> chat_node;
        chat_node -.-> __end__;
        chat_node -.-> tools;
        tools --> chat_node;
        classDef default fill:#f2f0ff,line-height:1.2
        classDef first fill-opacity:0
        classDef last fill:#bfb6fc