# 内置美食配图

本目录包含 20 张用于插件推荐回复的 AI 生成食物示意图。生成日期：2026-11-09；生成方式：Codex 内置 image_gen 工具，每张图片独立生成。

图片按默认食物库中的完整名称命名，插件重载时自动扫描并绑定。文件为工具返回的原始 PNG；下表列出实际尺寸与大小。

| 食物 | 图片文件 | 实际尺寸 | 大小 |
| --- | --- | --- | --- |
| 黄焖鸡米饭 | [黄焖鸡米饭.png](黄焖鸡米饭.png) | 1254 × 1254 | 2.48 MiB |
| 麻辣烫 | [麻辣烫.png](麻辣烫.png) | 1254 × 1254 | 2.66 MiB |
| 螺蛳粉 | [螺蛳粉.png](螺蛳粉.png) | 1254 × 1254 | 2.59 MiB |
| 炒饭 | [炒饭.png](炒饭.png) | 1254 × 1254 | 2.31 MiB |
| 水饺 | [水饺.png](水饺.png) | 1254 × 1254 | 2.03 MiB |
| 炸鸡 | [炸鸡.png](炸鸡.png) | 1254 × 1254 | 2.57 MiB |
| 汉堡 | [汉堡.png](汉堡.png) | 1254 × 1254 | 2.39 MiB |
| 披萨 | [披萨.png](披萨.png) | 1254 × 1254 | 2.62 MiB |
| 兰州拉面 | [兰州拉面.png](兰州拉面.png) | 1254 × 1254 | 2.44 MiB |
| 重庆小面 | [重庆小面.png](重庆小面.png) | 1254 × 1254 | 2.49 MiB |
| 馄饨 | [馄饨.png](馄饨.png) | 1254 × 1254 | 2.24 MiB |
| 煎饼果子 | [煎饼果子.png](煎饼果子.png) | 1254 × 1254 | 2.52 MiB |
| 肉夹馍 | [肉夹馍.png](肉夹馍.png) | 1254 × 1254 | 2.34 MiB |
| 烤冷面 | [烤冷面.png](烤冷面.png) | 1254 × 1254 | 2.71 MiB |
| 寿司 | [寿司.png](寿司.png) | 1254 × 1254 | 2.33 MiB |
| 煲仔饭 | [煲仔饭.png](煲仔饭.png) | 1254 × 1254 | 2.49 MiB |
| 卤肉饭 | [卤肉饭.png](卤肉饭.png) | 1254 × 1254 | 2.36 MiB |
| 酸菜鱼 | [酸菜鱼.png](酸菜鱼.png) | 1254 × 1254 | 2.43 MiB |
| 烧烤 | [烧烤.png](烧烤.png) | 1254 × 1254 | 2.88 MiB |
| 轻食沙拉 | [轻食沙拉.png](轻食沙拉.png) | 1254 × 1254 | 2.36 MiB |

其余食物在没有对应图片时继续发送文字推荐。上传的自定义配图可与这些内置配图一起使用。

## 生成提示词

每张图片的最终提示词由下方共用提示词、一个换行和对应的 Primary subject 描述组成。

### 共用提示词

```text
Use case: photorealistic-natural.
Asset type: a single square 1024x1024 opaque food photograph for a Chinese chatbot's food recommendation.
Style: photorealistic appetizing editorial food photography, natural food textures, soft warm window daylight, realistic colors without excessive saturation.
Scene: a clean light oak tabletop and softly blurred warm off-white background, restrained styling, no unrelated props.
Composition: slightly elevated three-quarter 45-degree view, the complete serving centered and fully inside the image, meal fills about 75 percent of the frame, sharp focus on the food, subtle shallow depth of field.
Constraints: one standalone meal photograph, no grid or collage, no text, no typography, no labels, no border, no brand names, no logos, no watermark, no hands or people.
```

### 黄焖鸡米饭

```text
Primary subject: A Chinese huangmenji chicken and rice meal: a small black clay casserole with tender braised chicken chunks, shiitake mushrooms, green bell pepper and glossy golden-brown savory sauce, accompanied by a small plain bowl of steamed white rice. Both casserole and rice bowl are fully in frame and form a single meal. The dish should look like real freshly cooked Chinese yellow-braised chicken.
```

### 麻辣烫

```text
Primary subject: A generous ceramic bowl of Chinese mala tang with inviting reddish spicy broth, fish balls, tofu puffs, sliced lotus root, enoki mushrooms, leafy bok choy and glass noodles. Ingredients are clearly recognizable, varied and naturally arranged; a few chili oil droplets glisten on the surface. No chopsticks stuck upright.
```

### 螺蛳粉

```text
Primary subject: A ceramic bowl of authentic Liuzhou luosifen rice noodles in reddish-orange broth, with long white rice noodles, crisp golden fried tofu skin, roasted peanuts, pickled bamboo shoots, pickled long beans and fresh green leafy vegetables. Distinct toppings arranged naturally, realistic rice noodle texture, appetizing chili oil sheen.
```

### 炒饭

```text
Primary subject: A single shallow off-white ceramic bowl of Chinese egg fried rice: separated golden rice grains, little pieces of scrambled egg, green scallions, tiny carrot cubes and green peas, with subtle wok-fried texture. A freshly served unbranded everyday Chinese fried rice meal.
```

### 水饺

```text
Primary subject: A plate of Chinese boiled pork-and-chive jiaozi dumplings (shui jiao), about ten plump crescent dumplings with delicate pleated edges, smooth moist ivory dough, no browned or fried surfaces. Arranged naturally on a plain off-white ceramic plate, with a tiny plain ceramic dipping dish of dark Chinese vinegar at the edge. Clearly authentic boiled Chinese dumplings.
```

### 炸鸡

```text
Primary subject: A plain ceramic plate of freshly fried chicken drumsticks and wings with a golden-brown craggy crisp coating, realistic flaky crunchy texture and appetizing subtle highlights. No red glaze or sauce coating, no fries, no branded packaging; the food itself is the focus.
```

### 汉堡

```text
Primary subject: One generous unbranded cheeseburger on a plain off-white ceramic plate: a golden sesame seed bun, a juicy grilled beef patty with melted cheddar, crisp green lettuce, a ripe tomato slice and a little burger sauce. Naturally assembled and believable, entire burger fully inside the frame. No fries, no drinks and no branded packaging.
```

### 披萨

```text
Primary subject: One whole round cheese and pepperoni pizza on a simple plain round off-white plate, golden oven-baked crust, gently browned melted mozzarella, a few evenly scattered pepperoni slices and fresh green basil leaves. Believable appetizing pizza textures, entire pizza and plate fully inside the square image. No pizza box, no utensils or unrelated food.
```

### 兰州拉面

```text
Primary subject: A large plain ceramic bowl of authentic Chinese Lanzhou hand-pulled beef noodles: fine springy wheat noodles in a clear golden beef broth, several tender thin beef slices, ivory daikon radish slices, fresh chopped cilantro and scallions, with just a small vivid red chili oil accent. The wheat noodles should be clearly visible and the broth should be clear rather than thick or milky.
```

### 重庆小面

```text
Primary subject: A ceramic bowl of Chongqing xiaomian, thin Chinese wheat noodles coated in a vivid red chili oil broth with fresh green bok choy, chopped scallions, a few roasted peanuts and finely sprinkled Sichuan chili flakes. A delicious modest everyday Chongqing spicy noodle serving, naturally arranged with the noodles clearly visible.
```

### 馄饨

```text
Primary subject: A ceramic bowl of Chinese pork wonton soup: about ten delicate ivory wontons with soft thin folded dough wrappers in a clear light golden broth, a little dark seaweed and finely chopped green scallions. Clearly wontons with loose silky wrappers, not round dumplings or noodles. Appetizing freshly cooked soup with subtle steam.
```

### 煎饼果子

```text
Primary subject: One freshly prepared Chinese jianbing guozi breakfast crepe on a plain ceramic plate, cut once to reveal its cross-section. A thin golden whole-grain egg crepe folded around a crisp fried cracker sheet, scallions, cilantro, a little lettuce and dark savory bean sauce. Show the contrast between the soft thin crepe and crunchy inner cracker; no meat patty, no cheese, no Western tortilla branding.
```

### 肉夹馍

```text
Primary subject: A Shaanxi roujiamo Chinese street-food sandwich on a plain off-white plate: a lightly toasted round wheat flatbread bun split open and generously stuffed with moist finely chopped slow-braised pork, with another half beside it to show the filling. Pale toasted Chinese flatbread, realistic braised meat fibers and juices, no lettuce, no cheese, no hamburger bun.
```

### 烤冷面

```text
Primary subject: A plate of Chinese grilled cold noodles street snack, kaolengmian: a supple flat noodle sheet grilled with egg and brushed with reddish-brown savory sauce, wrapped around a grilled sausage and chopped onion and cilantro, then sliced into appetizing bite-size rolls. Slightly browned edges and sauce sheen, clearly visible flat noodle-and-egg layers, on a simple ceramic plate.
```

### 寿司

```text
Primary subject: A restrained single-serving sushi assortment on a plain ceramic plate: four pieces of salmon nigiri with realistic silky orange salmon over compact white rice, plus four neat cucumber-and-salmon nori rolls with clearly defined cross-sections. A tiny dab of green wasabi and a little pickled ginger at the edge, no chopsticks, no branded sauce bottle, naturally appetizing food photography.
```

### 煲仔饭

```text
Primary subject: A Cantonese claypot rice meal in a small black earthenware pot: pearly rice with a slightly golden crisp edge, glossy slices of Chinese cured sausage, a few pieces of tender braised chicken, bright green bok choy and a fried egg with a soft golden yolk. A light sheen of soy sauce on the rice, realistic freshly cooked textures, entire claypot visible.
```

### 卤肉饭

```text
Primary subject: A single bowl of Taiwanese-style braised pork rice, luroufan: glossy small diced pieces of long-braised pork belly in rich brown soy gravy over steamed white rice, a halved soy-braised egg, pickled mustard greens and a few fresh bok choy leaves. The finely diced braised pork is the clear star of the dish, served in one plain ceramic bowl.
```

### 酸菜鱼

```text
Primary subject: A generous ceramic serving bowl of Chinese suancaiyu, fish with pickled mustard greens: delicate white fish slices in a light golden tangy broth, abundant pale green pickled mustard greens, a few dried red chili segments and green scallions. The fish should look moist and gently cooked, not fried; clear bright broth and recognizable pickled vegetables.
```

### 烧烤

```text
Primary subject: A delicious Chinese barbecue skewer platter on a plain ceramic plate: several wooden skewers of char-grilled lamb and beef with toasted cumin and chili flakes, a couple of mushroom skewers and grilled green pepper pieces. Realistic browned meat with subtle char marks and a light oil sheen, all skewers fully inside the image, no flames, no beer, no branded packaging.
```

### 轻食沙拉

```text
Primary subject: One generous fresh light-meal salad in a shallow off-white bowl: crisp mixed green lettuce, cherry tomato halves, cucumber slices, colorful bell pepper, sweetcorn, tender sliced grilled chicken breast and a halved soft-boiled egg, with a very light clear dressing. Fresh realistic ingredient textures, balanced natural colors, no heavy creamy sauce or unrelated side dishes.
```
