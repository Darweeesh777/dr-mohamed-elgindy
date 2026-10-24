// Site interactions: mobile menu, header state, reveal-on-scroll and
// consultation form shortcuts. No dependencies.
(function () {
  'use strict';

  window.siteReady = true; // tells the fallback in base.html that scripts are running

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var header = document.querySelector('[data-header]');

  // Mobile menu
  var toggle = document.querySelector('[data-menu-toggle]');
  var menu = document.querySelector('[data-menu]');
  if (header && toggle && menu) {
    var label = toggle.querySelector('[data-menu-label]');
    var setOpen = function (open) {
      header.classList.toggle('is-open', open);
      toggle.setAttribute('aria-expanded', String(open));
      label.textContent = open ? toggle.dataset.labelClose : toggle.dataset.labelOpen;
    };
    toggle.addEventListener('click', function () {
      setOpen(toggle.getAttribute('aria-expanded') !== 'true');
    });
    menu.addEventListener('click', function (event) {
      if (event.target.closest('a')) setOpen(false);
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && header.classList.contains('is-open')) {
        setOpen(false);
        toggle.focus();
      }
    });
    window.matchMedia('(min-width: 1101px)').addEventListener('change', function (event) {
      if (event.matches) setOpen(false);
    });
  }

  // Header border once the page scrolls
  if (header) {
    var onScroll = function () { header.classList.toggle('is-scrolled', window.scrollY > 8); };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  // Reveal sections as they enter the viewport
  var revealItems = document.querySelectorAll('.reveal');
  if (reduceMotion || !('IntersectionObserver' in window)) {
    revealItems.forEach(function (el) { el.classList.add('is-visible'); });
  } else {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    revealItems.forEach(function (el) { observer.observe(el); });
  }

  // YouTube player (privacy-enhanced). Nothing from YouTube loads until a
  // visitor chooses to watch.
  var isVideoId = function (id) { return /^[A-Za-z0-9_-]{11}$/.test(id || ''); };
  var makePlayer = function (id, title) {
    var iframe = document.createElement('iframe');
    iframe.src = 'https://www.youtube-nocookie.com/embed/' + id +
      '?autoplay=1&rel=0&hl=' + document.documentElement.lang;
    iframe.title = title || '';
    iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
    iframe.allowFullscreen = true;
    // YouTube needs the referring origin; the site's default policy would hide it.
    iframe.referrerPolicy = 'strict-origin-when-cross-origin';
    return iframe;
  };

  // Thumbnails: replaced in place by the player on click.
  document.querySelectorAll('[data-youtube-id]').forEach(function (link) {
    link.addEventListener('click', function (event) {
      var id = link.dataset.youtubeId;
      if (!isVideoId(id)) return;
      event.preventDefault();
      var iframe = makePlayer(id, link.dataset.title);
      var frame = document.createElement('div');
      frame.className = link.className; // keeps the size of the thumbnail it replaces
      frame.appendChild(iframe);
      link.replaceWith(frame);
      iframe.focus();
    });
  });

  // Pop-up player (case path explainers). Closing it removes the iframe, which
  // stops playback. Without <dialog> support the link opens YouTube instead.
  var dialog = document.querySelector('[data-video-dialog]');
  if (dialog && typeof dialog.showModal === 'function') {
    var dialogFrame = dialog.querySelector('.video-dialog__frame');
    var dialogTitle = dialog.querySelector('.video-dialog__title');
    var opener = null;
    document.querySelectorAll('[data-video-dialog-open]').forEach(function (link) {
      link.addEventListener('click', function (event) {
        var id = link.dataset.videoDialogOpen;
        if (!isVideoId(id)) return;
        event.preventDefault();
        opener = link;
        dialogTitle.textContent = link.dataset.title || '';
        dialogFrame.replaceChildren(makePlayer(id, link.dataset.title));
        dialog.showModal();
      });
    });
    dialog.querySelector('[data-video-dialog-close]').addEventListener('click', function () { dialog.close(); });
    dialog.addEventListener('click', function (event) {
      if (event.target === dialog) dialog.close(); // click on the backdrop
    });
    dialog.addEventListener('close', function () {
      dialogFrame.replaceChildren();
      if (opener) opener.focus();
    });
  }

  // "Watch" buttons start the matching player and bring it into view.
  document.querySelectorAll('[data-play]').forEach(function (button) {
    button.hidden = false; // hidden in the HTML: it needs JS to work
    button.addEventListener('click', function () {
      var thumb = document.querySelector('[data-youtube-id="' + button.dataset.play + '"]');
      if (!thumb) return;
      thumb.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'center' });
      thumb.click();
      button.hidden = true;
    });
  });

  // About page: the gold line grows with scrolling (--p from 0 to 1) and each
  // diamond lights up once the line reaches it.
  var timeline = document.querySelector('[data-timeline] .timeline__inner');
  if (timeline) {
    var markers = timeline.querySelectorAll('.tl-marker');
    var ticking = false;
    var updateTimeline = function () {
      ticking = false;
      var box = timeline.getBoundingClientRect();
      var progress = reduceMotion ? 1 : (window.innerHeight * 0.6 - box.top) / box.height;
      progress = Math.max(0, Math.min(1, progress));
      timeline.style.setProperty('--p', progress.toFixed(4));
      var tip = progress * box.height;
      markers.forEach(function (marker) {
        var m = marker.getBoundingClientRect();
        marker.classList.toggle('is-passed', m.top - box.top + m.height / 2 <= tip + 1);
      });
    };
    var requestUpdate = function () {
      if (!ticking) { ticking = true; window.requestAnimationFrame(updateTimeline); }
    };
    updateTimeline();
    window.addEventListener('scroll', requestUpdate, { passive: true });
    window.addEventListener('resize', requestUpdate);
  }

  // Article "copy link" button (shown only when the clipboard API is available).
  // The confirmation is announced in a live region next to the buttons.
  document.querySelectorAll('[data-copy-link]').forEach(function (button) {
    if (!navigator.clipboard) return;
    button.hidden = false;
    var status = document.getElementById(button.dataset.copiedTarget);
    var message = status && status.querySelector('span');
    var timer;
    button.addEventListener('click', function () {
      navigator.clipboard.writeText(button.dataset.copyLink).then(function () {
        button.classList.add('is-copied');
        if (message) message.hidden = false;
        clearTimeout(timer);
        timer = setTimeout(function () {
          button.classList.remove('is-copied');
          if (message) message.hidden = true;
        }, 2500);
      });
    });
  });
  // Consultation / appointment buttons: pick the request type and jump to the
  // form without reloading. Without JS the links reload with ?type=… instead.
  var form = document.querySelector('[data-consult-form]');
  if (form) {
    document.querySelectorAll('[data-request-type]').forEach(function (link) {
      link.addEventListener('click', function (event) {
        var option = form.querySelector('input[name="request_type"][value="' + link.dataset.requestType + '"]');
        if (!option) return;
        event.preventDefault();
        option.checked = true;
        document.getElementById('consultation').scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth' });
        history.replaceState(null, '', '#consultation');
        var first = form.querySelector('input[name="full_name"]');
        if (first) setTimeout(function () { first.focus({ preventScroll: true }); }, reduceMotion ? 0 : 600);
      });
    });

    // Static site: send the form to the Worker without leaving the page.
    if (form.hasAttribute('data-static-form')) {
      var status = form.parentNode.querySelector('[data-form-status]');
      var submit = form.querySelector('[type="submit"]');
      var show = function (text, ok) {
        status.textContent = text;
        status.className = 'notice ' + (ok ? 'notice--success' : 'notice--error');
        status.hidden = false;
        status.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'center' });
      };
      form.addEventListener('submit', function (event) {
        event.preventDefault();
        submit.disabled = true;
        fetch(form.action, { method: 'POST', body: new FormData(form) })
          .then(function (res) {
            if (res.ok) { form.reset(); show(form.dataset.msgSent, true); }
            else show(res.status === 400 ? form.dataset.msgInvalid : form.dataset.msgFailed, false);
          })
          .catch(function () { show(form.dataset.msgFailed, false); })
          .then(function () { submit.disabled = false; });
      });
    }

    if (form.hasAttribute('data-has-errors')) {
      var invalid = form.querySelector('[aria-invalid="true"]');
      if (invalid) invalid.focus();
    }
  }
})();
