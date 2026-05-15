import React from "react";
import { useLocation } from "react-router-dom";

import elephantLogo from "../../assets/brand/elephant-logo.png";
import { resolveNavigation } from "../../lib/dashboardNavigation";
import styles from "../RouteLayouts.module.css";

export function RoutePageHeader(): React.JSX.Element {
  const location = useLocation();
  const currentItem = resolveNavigation(location.pathname);

  return (
    <header className={styles.pageHeader} data-dashboard-page>
      <div className={styles.pageHeaderTop}>
        <div className={styles.pageHeaderCopy}>
          <div className={styles.pageHeaderBadges}>
            <span className={styles.pageHeaderBrandBadge}>
              <img src={elephantLogo} alt="" />
              <strong>Elephant Agent</strong>
            </span>
            <span className={styles.pageHeaderEyebrow}>{currentItem.eyebrow}</span>
          </div>
          <h1>{currentItem.title}</h1>
          <p>{currentItem.detail}</p>
        </div>
      </div>
    </header>
  );
}
