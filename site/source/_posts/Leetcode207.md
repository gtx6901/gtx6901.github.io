---
title: Leetcode随记-207课程表
date: 2026-03-10
categories:
  - 算法题
tags:
  - Leetcode
  - 图
math: true
permalink: /notes/Leetcode207/
---

#### 207. 课程表

难度：中等

---

你这个学期必须选修 `numCourses` 门课程，记为 `0` 到 `numCourses - 1` 。

在选修某些课程之前需要一些先修课程。 先修课程按数组 `prerequisites` 给出，其中 `prerequisites[i] = [ai, bi]` ，表示如果要学习课程 `ai` 则  **必须**  先学习课程  `bi` 。

*   例如，先修课程对 `[0, 1]` 表示：想要学习课程 `0` ，你需要先完成课程 `1` 。

请你判断是否可能完成所有课程的学习？如果可以，返回 `true` ；否则，返回 `false` 。

 **示例 1：** 

```
输入：numCourses = 2, prerequisites = [[1,0]]
输出：true
解释：总共有 2 门课程。学习课程 1 之前，你需要完成课程 0 。这是可能的。
```

 **示例 2：** 

```
输入：numCourses = 2, prerequisites = [[1,0],[0,1]]
输出：false
解释：总共有 2 门课程。学习课程 1 之前，你需要先完成​课程 0 ；并且学习课程 0 之前，你还应先完成课程 1 。这是不可能的。
```

 **提示：** 

*   `1 <= numCourses <= 2000`
*   `0 <= prerequisites.length <= 5000`
*   `prerequisites[i].length == 2`
*   `0 <= ai, bi < numCourses`
*   `prerequisites[i]` 中的所有课程对  **互不相同**

---

这是一个对于有向图的成环检测问题。我们先复习一下基础知识:

##### 图的表示

通常采用邻接表来储存(出)边
```c++
vector<vector<int>> adj;
for(vector<int>& edges:prerequisites){
    adj[edges[1]].push_back(edges[0]);
}
```

##### 有向图的成环检测

有向图的成环检测主要有两种经典思路：

1.  **DFS 状态标记法 (三色标记)**
    - **未访问 (0)**：初始状态。
    - **正在访问 (1)**：正在递归栈中。如果在 DFS 过程中重新遇到了状态为 1 的节点，说明出现了**后向边**，即存在环。
    - **已完成 (2)**：节点及其所有邻居都已遍历完毕。
2.  **BFS 入度法 (Kahn 算法)**
    - 统计所有节点的**入度**。
    - 始终将入度为 0 的节点加入队列（即没有任何先修条件的课程）。
    - 依次弹出节点并减小其邻居的入度。
    - 若最终处理的节点数小于总数，则说明剩下的节点相互依赖形成环。

---
初版：
```c++
class Solution {
public:
    bool canFinish(int numCourses, vector<vector<int>>& prerequisites) {
        vector<vector<int>> adj(numCourses);
        vector<int> indegree(numCourses,0);
        for(vector<int>& edges:prerequisites){
            // 计算入度
            indegree[edges[0]]++;
            adj[edges[1]].push_back(edges[0]);
        }

            int over = 1;
            int all_OK = 1;
            for(int i = 0; i<numCourses;i++){
                if(indegree[i] != -1){
                    all_OK = 0;
                }
                if(indegree[i] == 0){
                    over = 0;
                    indegree[i] = -1;
                    for(int& edge_to_delete:adj[i]){
                        indegree[edge_to_delete]--;
                    }
                }
            }
            // 边界条件
            if(all_OK){
                return true;
            }
            if(over){
                return false;
            }
        }
    }
};
```
- 用时:16.5% 内存:95.58%
>问题在于使用逐轮扫描的方式来模拟拓扑排序,最坏情况下，需要执行 O(n) 轮（每轮至少处理一个节点），每轮扫描 n 个节点，总时间复杂度 O(n²)。没有额外的队列或栈，因此内存占用较低。

**优化**:
```c++
class Solution {
public:
    bool canFinish(int numCourses, vector<vector<int>>& prerequisites) {
        vector<vector<int>> adj(numCourses);
        vector<int> indegree(numCourses,0);
        for(vector<int>& edges:prerequisites){
            // 计算入度
            indegree[edges[0]]++;
            adj[edges[1]].push_back(edges[0]);
        }
        // 维护一个队列用来记录入度为0的点
        queue<int> q;
        for(int i = 0; i<numCourses;i++){
            if(indegree[i] == 0){
                q.push(i);
            }
        }

        int processed =0;
        while(!q.empty()){
            int u = q.front(); 
            q.pop();
            processed++;
            for(int& edge_to_delete:adj[u]){
                indegree[edge_to_delete]--;
                if(indegree[edge_to_delete] == 0){
                    q.push(edge_to_delete);
                }
            }
        }
        return processed == numCourses;
        
    }
};
```
- 用时:84.63% 内存:66.83%