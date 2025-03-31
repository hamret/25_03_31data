const { chromium } = require('playwright');
const xlsx = require('xlsx');
const fs = require('fs');

/**
 * 브라우저를 여러개 열어서 동시에 여러 상품들을 크롤링 할 수 있게 해놨는데,
 * 비정상적인 트래픽 발생하면 차단될 수 있어서 링크 하나씩 크롤링 하는 것을 권장
 */

const targetUrls = [
  //'https://www.musinsa.com/review/goods/3405530',
  //'https://www.musinsa.com/review/goods/3987163',
  'https://www.musinsa.com/review/goods/3046316',
  // 'https://www.musinsa.com/review/goods/3325842',
  // 'https://www.musinsa.com/review/goods/3325842',
  // 'https://www.musinsa.com/review/goods/3325842',
  // 'https://www.musinsa.com/review/goods/3325842',
];

startWorking(targetUrls);

// 크롤링 및 데이터 저장해주는 함수
async function startWorking(targetUrls) {
  checkResultFolder();

  if (targetUrls.length > 2) {
    console.log('최대 2개 페이지만 크롤링이 가능합니다.');
    console.log('rate-limit가 걸릴 수 있음.');
    return;
  }

  //크롤링 함수 비동기로 시작
  const workingCrawling = targetUrls.map((url, index) =>
    startCrawling(url, index).catch((e) => {
      console.log(`에러가 발생해서 ${url}해당 주소의 크롤링이 중지됐습니다`);
      console.log(e);
      return null;
    })
  );

  //비동기로 시작된 크롤링 작업들을 기다림
  //아래처럼 결과 값을 가져옴
  //ex) const finishedCrawling = [{status:fullfilled, value: 값}]
  const finishedCrawling = await Promise.allSettled(workingCrawling);

  // 파일로 저장하는 부분
  finishedCrawling.forEach((result, index) => {
    const { value } = result;
    if (value === null) return;
    const { savedReviews, title } = value;

    console.log(`${title} 결과 파일에 저장중...`);

    const match = targetUrls[index].match(/(\d+)$/);
    const productNumber = match
      ? match[0]
      : Math.floor(Math.random() * (10000000 - 1) + 1);

    saveDataToXlsx(String(productNumber), title, [...savedReviews.values()]);
  });
}

/**
 * 크롤링하는 함수
 * @param {string} webUrl 크롤링할 상품 후기 url
 * @param {number} index
 * @returns
 */
async function startCrawling(webUrl, index = 0) {
  // 크롤링 결과 저장하는 Map
  const savedReviews = new Map();

  // Launch a new browser instance
  const browser = await chromium.launch({ headless: false });
  const browserContextOptions = {
    viewport: { width: 1200, height: 1100 },
    userAgent:
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
  };

  // 브라우저랑 페이지 준비
  const context = await browser.newContext(browserContextOptions);
  const page = await context.newPage();

  // 페이지 이동
  await page.goto(webUrl);

  const pageTitle = (await page.title()).replace(' | 무신사', '');
  console.log(
    `----- ${
      index + 1
    } 번째 url ${pageTitle} 페이지의 상품 후기 크롤링을 시작합니다. -----`
  );

  // 전체 상품 후기 드롭박스 클릭
  await clickAllProductReviews(page);
  await page.waitForTimeout(1000);

  // const allProductReviewsCount = await findElementBySelector(
  //   page,
  //   '.GoodsReviewOtherColorSection__DropdownTriggerInputSubText-sc-unsz7z-7.hhymsm.font-pretendard'
  // );
  // findElementBySelector에서 page.getByText를 사용해 정규표현식으로 찾아오도록 변경
  const allProductReviewsCount = await page.getByText(/상품 후기 \(\d+\)/);
  const allProductReviewsCountText = await allProductReviewsCount.textContent();
  const countReg = /\((.+)\)/; ///\((\d+)\)/;

  const match = allProductReviewsCountText.trim().match(countReg);
  const allCount = Number(match[1].replaceAll(',', ''));
  console.log(`${pageTitle}의 상품 후기 개수: ${allCount}`);

  // 무한 스크롤을 트리거 element. 해당 요소가 보이면 데이터를 가져옴,
  // height가 0인 요소는 locator로 찾을 수 없어서 $사용
  const infinityContainer = await page.$(
    '[data-viewport-type="window"] > div:nth-child(2)'
  );

  while (savedReviews.size < allCount) {
    console.log(
      `${pageTitle} while roofing currentSize::: ${savedReviews.size}, targetSize::: ${allCount}`
    );

    // 상품리스트 컨테이너 data-testid="virtuoso-item-list"
    const reviewList = await findElementBySelector(
      page,
      '[data-testid="virtuoso-item-list"]'
    );

    const reviews = reviewList.locator('> div');
    const currentReviewsCount = await reviews.count();

    for (let i = 0; i < currentReviewsCount; i++) {
      const review = reviews.nth(i);

      // evaluate메서드는 브라우저 내부에서 함수를 실행시켜줌. 리턴 값을 노드에서 사용할 수 있음
      const crawlResult = await review
        .evaluate((r) => {
          // 해당 콜백함수는 브라우저에서 실행됨.

          // element를 찾아 text를 가져오는 함수
          function getTextBySelector(element, selector) {
            const el = element.querySelector(selector);

            if (el === null) {
              return null;
            }

            const text = el.textContent.replaceAll('\n', ' ').trim();
            return text;
          }

          const dataIndex = Number(r.getAttribute('data-index'));

          const nickname = getTextBySelector(
            r,
            '.text-body_13px_med.font-pretendard'
          );

          const userInfos = r.querySelectorAll(
            'li > span.text-body_13px_reg.text-gray-600.font-pretendard'
          );

          let gender = (height = weight = productSize = null);

          // 성별, 키, 몸무게가 비어져있는 리뷰도 있어서 분기처리
          if (userInfos.length === 4) {
            // length가 4면 모두 기입된 경우
            for (let i = 0; i < 4; i++) {
              const info = userInfos[i];
              if (i === 0) {
                gender = info.textContent;
              } else if (i === 1) {
                height = info.textContent;
              } else if (i === 2) {
                weight = info.textContent;
              } else if (i === 3) {
                productSize = info.textContent[0];
              }
            }
          } else {
            // 구매 사이즈만 있는 경우
            productSize = userInfos[0].textContent[0];
          }

          const score = getTextBySelector(
            r,
            '.text-body_14px_semi.font-pretendard'
          );

          const date = getTextBySelector(
            r,
            '.text-body_13px_reg.GoodsReviewListItemInfo__ReviewCreateAtText-sc-1nltm0g-3.btA-DQP.text-gray-600.font-pretendard'
          );

          const content = getTextBySelector(
            r,
            '[data-button-name="후기내용"] > p'
          );

          const likeCount = getTextBySelector(
            r,
            '.ReviewListItemLikeButton__LikeIconContainer-sc-uwzf5l-0 > span.text-body_13px_reg.font-pretendard'
          );
          return {
            dataIndex,
            nickname,
            gender,
            height,
            weight,
            productSize,
            score,
            date,
            content,
            likeCount,
          };
        })
        .catch((e) => {
          // 요소를 찾을 수 없으면 null처리시킴
          console.log(
            '리뷰를 찾을 수 없어서 해당 상품 리뷰는 null 처리됐습니다.'
          );
          console.error(e);
          return null;
        });

      if (crawlResult === null)
        // 하나의 리뷰를 크롤링한 값이 null이면 그냥 null로 저장
        savedReviews.set(savedReviews.size, {
          dataIndex: null,
          nickname: null,
          gender: null,
          height: null,
          weight: null,
          productSize: null,
          score: null,
          date: null,
          content: null,
          likeCount: null,
        });
      else savedReviews.set(crawlResult.dataIndex, crawlResult);
    }

    // 스크롤을 맨 아애로 이동시키는 메서드
    await infinityContainer.scrollIntoViewIfNeeded();
    // 스크롤을 맨 아래로 이동시켰을 때 데이터 로드를 기다림, 이건 컴퓨터 사양 고려해서 값을 바꿔줘야함.
    await page.waitForTimeout(900);
  }

  console.log(
    `----- ${pageTitle} 크롤링 끝 찾은 리뷰 후기 개수::: ${savedReviews.size} ------`
  );
  await browser.close();

  return {
    title: pageTitle,
    savedReviews,
  };
}

/**
 * 전체 상품 후기 클릭하는 함수
 * @param {import('playwright').Page} page
 */
async function clickAllProductReviews(page) {
  await findElementAndClick(page, '[data-content-name="후기필터노출"]');
  await findElementAndClick(page, '[data-filter-value="전체상품보기"]');
}

/**
 * 선택자를 이용해 element를 찾아 클릭하는 함수
 * @param {import('playwright').Page} page
 * @param {string} selector
 */
async function findElementAndClick(page, selector) {
  console.log(`선택자가 ${selector}인 요소를 찾는 중 입니다.`);
  const element = await findElementBySelector(page, selector);
  await element.click();
}

/**
 * 선택자로 element 찾기
 * @param {import('playwright').Page} page
 * @param {string} selector
 * @returns
 */
async function findElementBySelector(page, selector) {
  try {
    const element = page.locator(selector);
    await element.waitFor();

    return element;
  } catch (e) {
    console.log(
      `해당 선택자:${selector}의 element를 찾을 수 없어 크롤링이 종료됩니다.`
    );
    console.log(e);
    await page.close();
  }
}

// 결과를 저장할 폴더를 확인하는 함수 없으면 만듬
function checkResultFolder() {
  fs.readdir('./result', (err) => {
    if (err) {
      console.error('result 폴더가 없어 result 폴더를 생성합니다.');
      fs.mkdirSync('result');
    }
  });
}

// csv로 저장하는 함수
function saveDataToXlsx(productNumber, title, data) {
  try {
    const worksheet = xlsx.utils.json_to_sheet(data);
    const workbook = xlsx.utils.book_new();
    xlsx.utils.book_append_sheet(workbook, worksheet, productNumber.toString());
    xlsx.writeFileAsync(
      `./result/${productNumber.toString()}.csv`,
      workbook,

      {
        bookType: 'csv',
        compression: true,
      },
      () => {
        console.log(`${title} 결과 파일에 저장 끝..`);
      }
    );
  } catch (e) {
    console.log(`${title} 파일 저장중 에러가 발생했습니다.`);
    console.error(e);
  }
}
