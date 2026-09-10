const syntaxHighlight = require("@11ty/eleventy-plugin-syntaxhighlight");

module.exports = function (eleventyConfig) {
  eleventyConfig.addPlugin(syntaxHighlight);
  eleventyConfig.addPassthroughCopy({ "assets/styles.css": "assets/styles.css" });
  eleventyConfig.addPassthroughCopy({ "site/assets/app.js": "assets/app.js" });
  eleventyConfig.addPassthroughCopy({ "site/assets/images": "assets/images" });
  eleventyConfig.addPassthroughCopy({ "site/assets/videos": "assets/videos" });
  eleventyConfig.addPassthroughCopy({ "site/assets/downloads": "assets/downloads" });

  return {
    dir: {
      input: "site",
      includes: "_includes",
      output: "_site"
    },
    markdownTemplateEngine: "njk"
  };
};
