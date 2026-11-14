import { Component } from "react";

// A crash in one feature shows a small notice instead of blanking the demo.
export default class FeatureBoundary extends Component {
  state = { error: null };
  static getDerivedStateFromError(error) {
    return { error };
  }
  render() {
    if (this.state.error) {
      return (
        <div className="feature-error">
          <strong>{this.props.title}</strong> hit a problem and was skipped.
          <pre>{String(this.state.error.message || this.state.error)}</pre>
        </div>
      );
    }
    return this.props.children;
  }
}
