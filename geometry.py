# geometry.py
from random import randint
from const import *
from shapely import Polygon as poly
from shapely.ops import unary_union

class Point: 
    def __init__(self,x,y):
        self.x = x
        self.y = y
    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)
    def __repr__(self):
        return f"Point({self.x}, {self.y})"
    def __mul__(self, other):
        if isinstance(other,Point):
            return self.x * other.y - self.y * other.x
        else:
            return Point(self.x * other,self.y * other)
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y
    def __lt__(self, other):
        if self.x == other.x:
            return self.y < other.y
        return self.x < other.x
    def len2(self):
        return self.x * self.x + self.y * self.y
    def __sub__(self, other):
        if isinstance(other,Point):
            return Point(self.x - other.x,self.y - other.y)
        return NotImplemented

def randPoint():
    return Point(randint(5,GRID_WIDTH - 15),randint(5,GRID_HEIGHT - 15))

def in_seg(p,a,b):
    if (b - a) * (p - a) != 0:
        return False
    if a.x == b.x:
        return min(a.y,b.y) < p.y and p.y < max(a.y,b.y)
    return min(a.x,b.x) < p.x and p.x < max(a.x,b.x)
    
def is_cross_in(a,b,c,d):
    if a == c or a == d or b == c or b == d:
        return False
    if ((b - a) * (d - a)) * ((b - a) * (c - a)) >= 0:
        return False
    if ((c - d) * (b - c)) * ((c - d) * (a - c)) >= 0:
        return False
    return True

def is_cross(a,b,c,d):
    if b == c or b == d:
        a,b = b,a
    if a == d:
        c,d = d,c # если равенство то a == c
    if a == c:
        if (b - a) * (d - a) == 0:
            return True
        return False
    if in_seg(c,a,b) or in_seg(d,a,b) or in_seg(a,c,d) or in_seg(b,c,d):
        return True
    return is_cross_in(a,b,c,d)

def tri_eq(fa,fb,fc,sa,sb,sc):
    return fa.len2() == sa.len2() and fb.len2() == sb.len2() and fc.len2() == sc.len2()
def tri_eq_dec(fa,fb,fc,sa,sb,sc):
    return tri_eq(fa - fb,fa - fc,fb - fc,sa - sb,sa - sc,sb - sc)

class Polyline:
    def __init__(self):
        self.arr = []
    def append(self,point):
        if not isinstance(point,Point):
            return
        self.arr.append(point)
    def size(self):
        return len(self.arr)
    def pop(self):
        self.arr.pop()
    def clear(self):
        self.arr.clear()



class Polygon:
    def __init__(self, lst = []):
        self.arr = lst # list точек
    def push_back(self,pt):
        self.arr.apend(pt)
    

    def size(self):
        return len(self.arr)
    def cross_edg(self,fp,fs):
        flag = False
        for i in range(0, len(self.arr)):
            if is_cross(fp,fs,self.arr[i - 1],self.arr[i]):
                flag = True
                break
        return not flag
    def area(self):
        ans = 0
        for i in range(self.size()):
            ans += self.arr[i - 1] * self.arr[i]
        return abs(ans)
    def random(self, size):
        self.arr.clear()
        if size < 3: 
            return ValueError
        while len(self.arr) <= 2:
            self.arr.append(randPoint())
            
            if len(self.arr) > 2 and (self.arr[1] - self.arr[0]) * (self.arr[2] - self.arr[0]) == 0:
                self.arr.pop() 
            if(len(self.arr) == 2 and self.arr[0] == self.arr[1]):
                self.arr.pop()
        cnt = 0
        while len(self.arr) < size:
            cnt += 1
            if cnt > self.size() * self.size() * 10:
                return self.random(size)
            ind = randint(1,len(self.arr) - 1)
            p = randPoint()
            flag = False
            for i in self.arr:
                if i == p:
                    flag = True
                    break
            if flag:
                continue
            #print(p.x,p.y)
            if self.cross_edg(self.arr[ind - 1], p) and self.cross_edg(self.arr[ind], p):
                self.arr.insert(ind,p)
    def is_in(self, pt):
        if self.fined_pos(pt) != -1:
            return True
        inf_point = Point(pt.x + PRIME_F,pt.y + PRIME_S)
        count = 0
        for i in range(len(self.arr)):
            if is_cross_in(self.arr[i - 1],self.arr[i],pt,inf_point):
                count += 1
        return count % 2 == 1
    def is_strictly_in(self,point):
        for i in range(self.size()):
            if (self.arr[i - 1] - point) *(self.arr[i] - point) == 0:
                return False
        return self.is_in(point)

    def is_in_edg(self,f,s):
        if not self.is_in(Point((f.x + s.x) / 2,(f.y + s.y) / 2)):
            return False
        for i in range(self.size()):
            if is_cross_in(self.arr[i - 1],self.arr[i],f,s):
                return False
        return True
    def __eq__(self, other):
        if not isinstance(other,Polygon):
            return False
        if self.area() != other.area():
            return False
        if(other.size() != self.size()):
            return False
        n = self.size()
        for i in range(n):
            flag = True
            for j in range(2, n):
                if not tri_eq_dec(self.arr[0],self.arr[j - 1],self.arr[j],other.arr[i] ,other.arr[(i + j - 1) % n], other.arr[(i + j) % n]):
                    flag = False
                    break
            if flag:
                return True
            flag = True
            for j in range(2,n):
                if not tri_eq_dec(self.arr[0],self.arr[j - 1],self.arr[j],other.arr[i] ,other.arr[(i - j + n + 1) % n], other.arr[(i - j + n) % n]):
                    flag = False
                    break
            if(flag):
                return True
        return False
    
    def cross(self,other):
        for p in other.arr:
            if self.is_strictly_in(p):
                return True
        for p in self.arr:
            if other.is_strictly_in(p):
                return True
        for i in range(self.size()):
            for j in range(other.size()):
                if is_cross_in(self.arr[i - 1],self.arr[i],other.arr[j - 1],other.arr[j]):
                    return True
        return False
    def delete(self):
        ans = []
        for i in self.arr:
            if len(ans) == 0 or (i != ans[-1] and i != ans[0]):
                ans.append(i)
        ans,self.arr = self.arr,ans
        ans.clear()
        if(self.size() < 2):
            self.arr = ans
            return
        for i in range(self.size()):    
            if (self.arr[i - 2] - self.arr[i - 1]) * (self.arr[i - 1] - self.arr[i]) != 0:
                ans.append(self.arr[i - 1])
        self.arr = ans
    def __add__(self, other):
        pl1 = poly([(p.x, p.y) for p in self.arr])        
        pl2 = poly([(p.x, p.y) for p in other.arr])        
        if pl1.intersects(pl2) and not pl1.touches(pl2):
            return self
        un = pl1 | pl2
        if un.geom_type == 'MultiPolygon':
            un = max(un.geoms, key=lambda p: p.area)
        un = un.exterior.coords[:-1]
        ans = Polygon([Point(int(x), int(y)) for x, y in un])
        ans.delete()
        return ans
    def swap(self):
        for i in range(self.size()):
            self.arr[i].x, self.arr[i].y = self.arr[i].y ,self.arr[i].x
    def minusx(self):
        for i in range(self.size()):
            self.arr[i].x = -self.arr[i].x
    def minusy(self):
        for i in range(self.size()):
            self.arr[i].y = - self.arr[i].y
    def sim(self, n):
        if (n & 1):
            self.swap()
        if (n & 2):
            self.minusx()
        if (n & 4):
            self.minusy()

    def is_corect(self):
        for i in range(self.size()):
            for j in range(i + 1,self.size()):
                if self.arr[i] == self.arr[j]:
                    return False
                if is_cross(self.arr[i - 1],self.arr[i],self.arr[j - 1],self.arr[j]):
                    return False
        return True
    def sdvig(self,min_x,min_y):
        for i in range(self.size()):
            self.arr[i].x -= min_x
            self.arr[i].y -= min_y
    def complexity_corect(self,complexity):
        if complexity == 2 :
            return True
        if self.size() % 2:
            return True
        for i in range(self.size()):
            for j in range(i + 2, self.size()):
                if i == 0 and j == self.size() - 1:
                    continue
                if not self.is_in_edg(self.arr[i], self.arr[j]):
                    continue
                if((i - j) * 2 == self.size()):
                    continue
                p = [self.arr[i]]
                q = [self.arr[j]]
                u = i
                while u != j:
                    u = u + 1
                    if u == self.size():
                        u -= self.size()
                    p.append(self.arr[u])
                while u != i:
                    u = u + 1
                    if u == self.size():
                        u -= self.size()
                    q.append(self.arr[u])
                if Polygon(p) == Polygon(q):
                    return False
        return True

        
                        

    def generate(self, complexity):
        # for i in range(self.size()):
        #     print(self.arr[i])
        #complexity += 3
        cnt = 0
        while True:
            cnt += 1
            size = randint(2,3) + complexity
            self.random(size)
            if cnt > 1000000:
                print("GENERATE ERROR")
            for i in range(1,8):
                other = Polygon([Point(p.x, p.y) for p in self.arr])
                other.sim(i)
                for j in range(other.size()):
                    nxt = j + 1
                    if nxt == other.size():
                        nxt -= other.size()
                    if complexity > 3:
                        if (self.arr[-1] - self.arr[0]) * (other.arr[j - 1] - other.arr[j]) != 0 or (self.arr[0] - self.arr[1]) * (other.arr[j] - other.arr[nxt]):
                            continue
                    vec = self.arr[0] - other.arr[j]
                    for u in range(other.size()):
                        other.arr[u] = other.arr[u] + vec
                    if self.cross(other):
                        continue
                    res = self + other
                    if (complexity + res.size() - self.size() * 2 < 1 or cnt > 1000000) and res.area() == self.area() + other.area() and res.is_corect() and ((res.complexity_corect(complexity)) or cnt > 1000000) :
                        print("============")
                        min_x, min_y = PRIME_F,PRIME_F
                        for i in res.arr:
                            min_x,min_y = min(min_x,i.x),min(min_y,i.y)
                        self.sdvig(min_x,min_y)
                        res.sdvig(min_x,min_y)
                        other.sdvig(min_x,min_y)
                        for i in self.arr:
                            print(i)
                        print("-----------")
                        for i in other.arr:
                            print(i)
                        print("-----------")    
                        return res,self,other
    def fined_pos(self,point):
        if not isinstance(point,Point):
            return -1
        for i in range(self.size()):
            if in_seg(point,self.arr[i - 1],self.arr[i]) or point == self.arr[i]:
                return i
        return -1
    def draw_line(self,line):
        if not self.is_in(line.arr[-1]):
            print("point is not in polygon")
            return False
        if line.size() < 2:
            return True
        if not self.is_in_edg(line.arr[-1], line.arr[-2]):
            return False
        for i in range(line.size() - 2):
            if is_cross_in(line.arr[i], line.arr[i + 1], line.arr[-1], line.arr[-2]):
                return False
        return True

    def is_line_correct(self,line):
        if not isinstance(line,Polyline):
            print("Line is not Polyline")
            return False
        if line.size() < 2:
            print("Line has less than 2 points")
            return False
        begin = self.fined_pos(line.arr[0])
        if begin == -1:
            print(f"Start point {line.arr[0]} not on polygon edge")
            return False
        end = self.fined_pos(line.arr[-1])
        if end == -1:
            print(f"End point {line.arr[-1]} not on polygon edge")
            return False
        cnt = 0
        for i in line.arr[1:-1]:  # intermediate points should be inside or on boundary
            if not self.is_strictly_in(i) and self.fined_pos(i) == -1:
                cnt += 1
        # Allow intermediate points on boundary or outside (removed strict check)

        for i in range(line.size() - 1):
            if not self.is_in_edg(line.arr[i], line.arr[i + 1]):
                print(f"Edge {line.arr[i]} to {line.arr[i + 1]} not valid")
                return False
        print("Line is correct")
        return True
    
    
    def divide(self, line):
        if not self.is_line_correct(line):
            return -1
        
        begin,end = self.fined_pos(line.arr[0]),self.fined_pos(line.arr[-1])
        first = []
        second = []
        i = begin
        while i != end:
            first.append(self.arr[i])
            i += 1
            if i == self.size():
                i -= self.size()
        for j in line.arr[::-1]:
            first.append(j)
        while i != begin:
            second.append(self.arr[i])
            i += 1
            if i == self.size():
                i -= self.size()
        for j in line.arr:
            second.append(j)
        first = Polygon(first)
        second = Polygon(second)
        first.delete()
        second.delete()
        return first,second

def is_true_divide(poly,line):
    if not poly.is_line_correct(line):
        return False
    first,second = poly.divide(line)
    if first == -1:
        return False
    print(f"First polygon: {first.arr}")
    print(f"Second polygon: {second.arr}")
    print(f"First area: {first.area()}, Second area: {second.area()}")
    result = first == second
    print(f"Are they equal? {result}")
    return result

    

                    


# import sys

# # Теперь любой input() будет брать данные из файла input.txt
# sys.stdin = open('in.txt', 'r')
    
# n = int(input())
# l = []
# for i in range(n):
#     s = input().replace("(", "").replace(")", "")
#     x, y = map(int, s.split(", "))
#     l.append(Point(x,y))
# poly = Polygon(l)
# line = Polyline()
# n = int(input())
# for i in range(n):
#     s = input().replace("(", "").replace(")", "")
#     x, y = map(int, s.split(","))
#     line.append(Point(x,y))
#     if line.size() > 1 and poly.draw_line(line):
#         print(f"Line is valid with new point ({x}, {y})")
# print(is_true_divide(poly,line))