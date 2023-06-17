import fetch from 'node-fetch';
import { HttpsProxyAgent } from 'https-proxy-agent';
import * as cheerio from 'cheerio';
import fs from 'fs/promises';

// ---配置部分---

const root = 'https://zh.wikipedia.org/zh-cn/'; // zh-cn变体
const root_pages = {
    'Category:数学定理': {depth: 6},
    'Category:数学概念': {depth: 5}, // 子分类很杂
    'Category:数学家': {depth: 6}, // 人名还是另做词典好
};
const proxy = 'http://127.0.0.1:1080';
const max_connection = 10;
const dict_name = 'wikipedia_zh_cn_math';
const head = `# Rime dictionary
# encoding: utf-8
# 未去重
---
name: ${dict_name}
version: ${new Date().toLocaleDateString('se')}
sort: by_weight
columns:
  - text
  - weight
...

`;
// function converter(entry: string): string[];
function converter(entry) {
    entry = entry.split(' ')[0]; // 'xxx (消歧义)' => 'xxx'
    let entries = entry.split('·'); // 分割人名 // 还是不分好，外文人名另外做词典
    return entries.filter(en => en.length > 1 && /^[\p{sc=Han}-]+$/u.test(en)); // 仅汉字或'-' 至少两个汉字
}

// ---配置结束---

let dict_file = await fs.open(`${dict_name}.dict.yaml`, 'w');
dict_file.write(head);
const proxy_agent = new HttpsProxyAgent(proxy);

let count = 0; // 连接计数
async function get_html(url) {
    while (count > max_connection) {
        await new Promise(f => setTimeout(f, 1500));
    }
    count += 1;
    const res = await fetch(url, { agent: proxy_agent });
    const html = await res.text();
    count -= 1;
    return html;
}

let visited = new Set();
async function crawl(page, depth = 0, depth_limit = 3) {
    if (depth > depth_limit) {
        return;
    }
    if (!page.startsWith('Category:') && page.includes(':')) {
        // 筛除'分类'以外命名空间的条目
        return;
    }

    let html;
    try {
        html = await get_html(`${root}${page}`);
    } catch (err) {
        console.log(err);
        return;
    }
    const $ = cheerio.load(html);
    const links = $('.mw-category-group').find('a');
    const title = $('#firstHeading').text();

    // 普通条目写入文件，'分类'条目遍历
    if ($('.mw-page-title-namespace').length == 0) {
        let entries = converter(title);
        for (let entry of entries) {
            dict_file.write(`${entry}\t100\n`);
        }
        return;
    } else {
        console.log(`In ${title}`);
    }

    let next_tasks = [];
    for (let elem of links) {
        const next_url = elem.attribs['href']; // '/wiki/xxxx'
        const next_page = next_url.slice('/wiki/'.length);
        if (visited.has(next_page)) {
            continue;
        }
        visited.add(next_page);
        next_tasks.push(crawl(next_page, depth + 1, depth_limit));
    }
    await Promise.all(next_tasks);
}

for (let root_page in root_pages) {
    await crawl(root_page, 0, root_pages[root_page].depth);
}
