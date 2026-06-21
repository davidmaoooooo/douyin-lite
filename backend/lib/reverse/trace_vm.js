// -*- coding: utf-8 -*-
/**
 * 用 Node.js inspector 动态追踪 JSVMP 执行
 *
 * 运行方式：
 * node --inspect-brk trace_vm.js
 * 然后在 Chrome DevTools 中设置断点
 */

const { get_a_bogus } = require('./lib/runtime/bdms/index.js');

// 测试用例
const TEST_CASES = [
    { T: 1700000000000, query: 'aweme_id=1' },
    { T: 1700000001000, query: 'aweme_id=1' },  // +1秒
    { T: 1700000100000, query: 'aweme_id=1' },  // +100秒
];

console.log('准备追踪 VM 执行...\n');

for (const tc of TEST_CASES) {
    const url = `https://www.douyin.com/aweme/v1/web/aweme/detail/?${tc.query}&_t=${tc.T}`;

    console.log(`\n=== 测试: T=${tc.T} ===`);

    // Hook Date.now
    const oldDateNow = Date.now;
    Date.now = () => tc.T;

    const result = get_a_bogus(url, '');

    console.log(`a_bogus: ${result.slice(0, 60)}...`);
    console.log(`长度: ${result.length}`);

    // 恢复
    Date.now = oldDateNow;
}

console.log('\n\n提示：');
console.log('1. bdms.js 是混淆代码，无法直接读懂');
console.log('2. 需要在运行时动态分析');
console.log('3. 或者用符号执行工具（angr/Triton）');
